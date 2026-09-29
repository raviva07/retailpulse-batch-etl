from pathlib import Path
import json, sqlite3, shutil
from src.pipeline import run, ROOT

def reset():
    for rel in ['data/bronze','data/silver','data/gold','warehouse','logs']:
        p=ROOT/rel
        if p.exists(): shutil.rmtree(p)
    (ROOT/'warehouse').mkdir()

def test_pipeline_end_to_end():
    reset()
    result=run(ROOT/'config.json')
    assert result['status']=='loaded'
    assert result['fact_rows']==8
    assert result['revenue']==12100.0
    conn=sqlite3.connect(ROOT/'warehouse/retailpulse.db')
    assert conn.execute('select count(*) from dim_customer').fetchone()[0]==5
    assert conn.execute('select count(*) from dim_product').fetchone()[0]==5
    conn.close()
    assert (ROOT/'data/gold/daily_sales.csv').exists()

def test_idempotent_rerun():
    reset(); run(ROOT/'config.json')
    second=run(ROOT/'config.json')
    assert second['status']=='skipped'
    assert second['fact_rows']==8

def test_fresh_checkout_and_gold_recovery():
    reset(); shutil.rmtree(ROOT/'warehouse')
    assert run(ROOT/'config.json')['fact_rows']==8
    shutil.rmtree(ROOT/'data/gold')
    assert run(ROOT/'config.json')['status']=='skipped'
    assert (ROOT/'data/gold/daily_sales.csv').exists()
