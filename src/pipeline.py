from __future__ import annotations
import argparse, hashlib, json, logging, shutil, sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()])

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def validate(df: pd.DataFrame) -> None:
    required = ['order_id','order_ts','customer_id','customer_name','city','product_id','product_name','category','quantity','unit_price']
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f'Missing columns: {missing}')
    if df['order_id'].duplicated().any(): raise ValueError('Duplicate order_id detected')
    if df[required].isna().any().any(): raise ValueError('Null required value detected')
    if (df['quantity'] <= 0).any() or (df['unit_price'] <= 0).any(): raise ValueError('Quantity and unit_price must be positive')

def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS pipeline_runs(run_id INTEGER PRIMARY KEY AUTOINCREMENT, source_hash TEXT UNIQUE, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP, row_count INTEGER);
    CREATE TABLE IF NOT EXISTS dim_customer(customer_key INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT UNIQUE, customer_name TEXT, city TEXT);
    CREATE TABLE IF NOT EXISTS dim_product(product_key INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT UNIQUE, product_name TEXT, category TEXT);
    CREATE TABLE IF NOT EXISTS dim_date(date_key INTEGER PRIMARY KEY, full_date TEXT UNIQUE, year INTEGER, month INTEGER, day INTEGER);
    CREATE TABLE IF NOT EXISTS fact_sales(order_id TEXT PRIMARY KEY, order_ts TEXT, date_key INTEGER, customer_key INTEGER, product_key INTEGER, quantity INTEGER, unit_price REAL, revenue REAL,
      FOREIGN KEY(customer_key) REFERENCES dim_customer(customer_key), FOREIGN KEY(product_key) REFERENCES dim_product(product_key), FOREIGN KEY(date_key) REFERENCES dim_date(date_key));
    ''')

def already_loaded(conn: sqlite3.Connection, source_hash: str) -> bool:
    return conn.execute('SELECT 1 FROM pipeline_runs WHERE source_hash=?', (source_hash,)).fetchone() is not None

def transform(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['order_ts'] = pd.to_datetime(out['order_ts'], utc=False)
    out['customer_name'] = out['customer_name'].str.strip().str.title()
    out['city'] = out['city'].str.strip().str.title()
    out['category'] = out['category'].str.strip().str.title()
    out['revenue'] = (out['quantity'] * out['unit_price']).round(2)
    out['order_date'] = out['order_ts'].dt.date.astype(str)
    return out

def load_warehouse(conn: sqlite3.Connection, df: pd.DataFrame, source_hash: str) -> None:
    with conn:
        for r in df.itertuples(index=False):
            conn.execute('INSERT INTO dim_customer(customer_id,customer_name,city) VALUES(?,?,?) ON CONFLICT(customer_id) DO UPDATE SET customer_name=excluded.customer_name, city=excluded.city', (r.customer_id,r.customer_name,r.city))
            conn.execute('INSERT INTO dim_product(product_id,product_name,category) VALUES(?,?,?) ON CONFLICT(product_id) DO UPDATE SET product_name=excluded.product_name, category=excluded.category', (r.product_id,r.product_name,r.category))
            d = pd.Timestamp(r.order_ts)
            date_key = int(d.strftime('%Y%m%d'))
            conn.execute('INSERT OR IGNORE INTO dim_date(date_key,full_date,year,month,day) VALUES(?,?,?,?,?)', (date_key,d.date().isoformat(),d.year,d.month,d.day))
            ck = conn.execute('SELECT customer_key FROM dim_customer WHERE customer_id=?',(r.customer_id,)).fetchone()[0]
            pk = conn.execute('SELECT product_key FROM dim_product WHERE product_id=?',(r.product_id,)).fetchone()[0]
            conn.execute('INSERT OR IGNORE INTO fact_sales(order_id,order_ts,date_key,customer_key,product_key,quantity,unit_price,revenue) VALUES(?,?,?,?,?,?,?,?)', (r.order_id,str(r.order_ts),date_key,ck,pk,int(r.quantity),float(r.unit_price),float(r.revenue)))
        conn.execute('INSERT INTO pipeline_runs(source_hash,row_count) VALUES(?,?)', (source_hash,len(df)))

def publish_gold(conn: sqlite3.Connection, gold_dir: Path) -> None:
    gold_dir.mkdir(parents=True, exist_ok=True)
    queries = {
      'daily_sales.csv': '''SELECT d.full_date, COUNT(*) orders, ROUND(SUM(f.revenue),2) revenue FROM fact_sales f JOIN dim_date d USING(date_key) GROUP BY d.full_date ORDER BY d.full_date''',
      'category_sales.csv': '''SELECT p.category, SUM(f.quantity) units, ROUND(SUM(f.revenue),2) revenue FROM fact_sales f JOIN dim_product p USING(product_key) GROUP BY p.category ORDER BY revenue DESC''',
      'city_sales.csv': '''SELECT c.city, COUNT(DISTINCT f.order_id) orders, ROUND(SUM(f.revenue),2) revenue FROM fact_sales f JOIN dim_customer c USING(customer_key) GROUP BY c.city ORDER BY revenue DESC'''
    }
    for name,q in queries.items():
        pd.read_sql_query(q,conn).to_csv(gold_dir/name,index=False)

def run(config_path: Path) -> dict:
    cfg = load_config(config_path)
    def p(key): return ROOT / cfg[key]
    setup_logging(p('log_file'))
    source = p('input_file'); source_hash = sha256(source)
    p('bronze_dir').mkdir(parents=True, exist_ok=True)
    bronze_copy = p('bronze_dir') / source.name
    shutil.copy2(source, bronze_copy)
    p('warehouse_db').parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p('warehouse_db')); conn.execute('PRAGMA foreign_keys=ON'); ensure_schema(conn)
    if already_loaded(conn, source_hash):
        publish_gold(conn, p('gold_dir'))
        logging.info('Idempotency: source already loaded; skipping.')
        facts = conn.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0]
        conn.close(); return {'status':'skipped','fact_rows':facts}
    raw = pd.read_csv(bronze_copy); validate(raw); clean = transform(raw)
    p('silver_dir').mkdir(parents=True, exist_ok=True)
    clean.to_csv(p('silver_dir')/'sales_clean.csv',index=False)
    load_warehouse(conn, clean, source_hash); publish_gold(conn,p('gold_dir'))
    facts = conn.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0]
    revenue = conn.execute('SELECT ROUND(SUM(revenue),2) FROM fact_sales').fetchone()[0]
    conn.close(); logging.info('Loaded %s facts; revenue=%s',facts,revenue)
    return {'status':'loaded','fact_rows':facts,'revenue':revenue}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default=str(ROOT/'config.json')); args=ap.parse_args()
    print(json.dumps(run(Path(args.config)),indent=2))
