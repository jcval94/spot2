# Cluster findings

Profiles passing balance and ARI gates: physical_profile, location_profile, broker_service_profile.
Rejected profiles: need_profile, dynamic_need_profile.

Only passing families enter the confirmatory combination table. 47
all-family cells were retained separately for audit, but not interpreted. Among
19 eligible cells, 0 pass BH-FDR 10%.

The inherited `DN4 × LOC1 × BSV1` pocket remains a pre-registered hypothesis only:
Dynamic Need failed the current balance gate and numeric cluster labels are not
stable semantic identities across refits. It is not used as a multiplier.

## Top eligible cells

```text
interaction,n,positives,visit_rate,smoothed_rate,lift_vs_global,wilson_low,wilson_high,p_value_one_sided,physical_profile,location_profile,broker_service_profile,fdr_reject_10pct
physical_profile x broker_service_profile,66,16,0.24242424242424243,0.23135004530353367,1.187596899224806,0.15509054458269061,0.35809357491056265,0.16433616343764418,PH3,,BSV2,False
physical_profile x broker_service_profile,68,16,0.23529411764705882,0.22609208972845335,1.1606060606060604,0.1503436437092872,0.34855393095497417,0.1996075152402716,PH3,,BSV3,False
physical_profile x broker_service_profile,92,21,0.22826086956521738,0.22228664192949907,1.1410714285714285,0.1544207850299761,0.32388508632442525,0.20890151283811312,PH1,,BSV3,False
physical_profile x broker_service_profile,59,13,0.22033898305084745,0.21387473286207462,1.0978902953586496,0.13354072524323757,0.3413294244665089,0.31022550234675206,PH2,,BSV3,False
location_profile x broker_service_profile,127,27,0.2125984251968504,0.2101775775245163,1.0789115646258503,0.15042374107946094,0.2916497279089954,0.3063238554535396,,LOC2,BSV3,False
physical_profile x broker_service_profile,90,18,0.2,0.19905548996458086,1.0218181818181817,0.130422969625965,0.29413927142704344,0.4504857467082206,PH1,,BSV2,False
physical_profile x broker_service_profile,152,30,0.19736842105263158,0.19707037148897613,1.011627906976744,0.14189466065483164,0.2677623243863897,0.46820144324481267,PH4,,BSV2,False
physical_profile x location_profile x broker_service_profile,56,11,0.19642857142857142,0.19600136705399862,1.006140350877193,0.11338480016444108,0.3184485732747718,0.4877649845924973,PH4,LOC2,BSV2,False
location_profile x broker_service_profile,67,13,0.19402985074626866,0.19420809075981488,0.9969348659003829,0.11705063857457097,0.3041933762415822,0.5063925273593756,,LOC3,BSV3,False
physical_profile x broker_service_profile,117,22,0.18803418803418803,0.18902265617594083,0.9703163017031629,0.12758105898852096,0.26832233851697385,0.5733560360166227,PH4,,BSV3,False
```
