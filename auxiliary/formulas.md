# 波段运算与分区公式

以下公式可作为ENVI Band Math、QGIS栅格计算器或ArcGIS Raster Calculator的复现依据。

## 热风险

```text
HeatRiskEarly = clip((LST_Early - P5_Early) / (P95_Early - P5_Early), 0, 1)
HeatRiskLate  = clip((LST_Late  - P5_Late)  / (P95_Late  - P5_Late),  0, 1)
HeatPersistence = 0.5 * HeatRiskEarly + 0.5 * HeatRiskLate
```

## 水涝风险

```text
WaterRisk = clip((WaterIndex - P5_Water) / (P95_Water - P5_Water), 0, 1)
```

## 复合风险

```text
CompoundRisk = 0.55 * HeatPersistence + 0.45 * WaterRisk
```

## 四类治理分区

```text
HeatHigh  = HeatPersistence >= 0.67
WaterHigh = WaterRisk >= 0.67

Zone = 1 + HeatHigh + 2 * WaterHigh
```

## 土地覆盖转换

```text
NewImpervious = Transition == 2
```

## 注意

`P5`和`P95`应由同一分析范围、同一有效像元口径计算；不得直接把不同年份或不同范围的原始温度最小—最大值混用。
