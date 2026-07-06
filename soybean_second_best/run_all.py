#!/usr/bin/env python3
"""全流程入口: M3→M1→M2→M4→M5→M6→M7→report。--fast 缩减抽样(<15分钟), --full 完整。"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    fast = not args.full

    from src import model_core as mc
    from src import io_aggregate, m3_network, m1_planner, m2_portfolio
    from src import m4_abm, m5_policy, m6_props, m7_sensitivity, report

    t0 = time.time()

    def tick(name):
        print(f"===== {name} 完成 ({time.time()-t0:.0f}s) =====", flush=True)

    io_aggregate.aggregate(); tick("IO聚合")
    m3_network.run(); tick("M3 网络")
    cfg = mc.load_cfg()
    m1_planner.run(cfg, fast=fast); tick("M1 规划")
    cfg = mc.load_cfg()   # 重载 derived
    m2_portfolio.run(cfg, fast=fast); tick("M2 组合")
    m4_abm.run_selfcheck(cfg, fast=fast); tick("M4 ABM 自检")
    m5_res = m5_policy.run(cfg, fast=fast); tick("M5 政策矩阵")
    props = m6_props.run(cfg, fast=fast, m5_res=m5_res); tick("M6 命题检验")
    m7_sensitivity.run(cfg, fast=fast); tick("M7 敏感性")
    report.run(cfg, meta=dict(mode="fast" if fast else "full")); tick("报告")
    n_pass = int(props.passed.sum())
    print(f"命题检验: {n_pass}/6 通过 | 总耗时 {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
