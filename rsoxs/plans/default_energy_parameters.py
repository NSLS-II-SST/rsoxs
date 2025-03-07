
## This is intended to contain a revised set of default parameters that would be used after refactoring the codebase


## These parameters would be fed into _make_gscan_points function in nbs_bl.plans.scan_base with the format (start, stop, step, stop, step, etc.)
## In general, these are intended to recreate the energy lists from Eliot's old plan
## TODO: ideally, I would like to import _make_gscan_points locally to test these scan parameters
energyListParameters = {
    "carbon_NEXAFS":  (250, 282, 1.45, 297, 0.3, 350, 1.45), ## This is intended to recreate edge=(250, 282, 297, 350), ratios=(5, 1, 5), frames=112 often used for carbon-edge NEXAFS
    "nitrogen_NEXAFS":  (370, 397, 1, 407, 0.2, 440, 0.95), ## Intended to recreate edge=(370, 397, 407, 440), ratios=(5, 1, 5), frames=112
    "oxygen_NEXAFS":  (500, 525, 1.1, 540, 0.2, 560, 1.1), ## Intended to recreate edge=(500, 525, 540, 560), ratios=(5, 1, 5), frames=112
    "fluorine_NEXAFS":  (650, 680, 1.5, 700, 0.3, 740, 1.5), ## Intended to recreate edge=(650, 680, 700, 740), ratios=(5, 1, 5), frames=112
    "magnesium_RSoXS":  (1250, 1300, 2.6, 1330, 0.5, 1430, 2.7), ## Intended to recreate edge=(1250,1300,1330,1430), ratios=(5, 1, 5), frames=112
    "aluminum_NEXAFS":  (1540, 1560, 1.6, 1580, 0.3, 1600, 1.6), ## Intended to recreate edge=(1500, 1560, 1580, 1600), ratios=(5, 1, 5), frames=112
    "silicon_NEXAFS":  (1820, 1840, 1.5, 1860, 0.3, 1910, 1.5), ## Intended to recreate edge=(1820,1840,1860,1910), ratios=(5, 1, 5), frames=112
    "sulfurL_NEXAFS":  (150, 160, 0.8, 170, 0.15, 200, 0.8), ## Intended to recreate edge=(150, 160, 170, 200), ratios=(5, 1, 5), frames=112
    "calciumL_NEXAFS":  (320, 345, 0.9, 355, 0.15, 380, 0.9), ## Intended to recreate edge=(320, 345, 355, 380), ratios=(5, 1, 5), frames=112
    "ironL_NEXAFS":  (680, 700, 2, 730, 0.35, 780, 2), ## Intended to recreate edge=(680,700,730,780), ratios=(5, 1, 5), frames=112
    "zincL_NEXAFS":  (1000, 1015, 1.5, 1035, 0.3, 1085, 1.45), ## Intended to recreate edge=(1000, 1015, 1035, 1085), ratios=(5, 1, 5), frames=112

    "carbon_RSoXS":  (250, 270, 5, 282, 1, 287, 0.1, 292, 0.2, 305, 1, 350, 5), ## Intended to recreate edge=(250, 270, 282, 287, 292, 305, 350), ratios=(5, 1, 0.1, 0.2, 1, 5), frames=112
    "nitrogen_RSoXS":  (380, 397, 0.3, 407, 0.1, 440, 0.3), ## Intended to recreate edge=(380, 397, 407, 440), ratios=(2, 0.2, 2), frames=112
    "oxygen_RSoXS":  (510, 525, 1.65, 540, 0.15, 560, 1.65), ## Intended to recreate edge=(510, 525, 540, 560), ratios=(2, 0.2, 2), frames=112
    "fluorine_RSoXS":  (670, 680, 1.65, 690, 0.15, 700, 0.5, 740, 1.65), ## Intended to recreate edge=(670, 680, 690, 700, 740), ratios=(2, 0.2, 0.6, 2), frames=112
    "magnesium_RSoXS":  (1250, 1300, 4.2, 1330, 0.4, 1430, 4), ## Intended to recreate edge=(1250,1300,1330,1430), ratios=(2, 0.2, 2), frames=112
    "aluminum_RSoXS":  (1540, 1560, 2.2, 1580, 0.2, 1600, 2.2), ## Intended to recreate edge=(1540, 1560, 1580, 1600), ratios=(2, 0.2, 2), frames=112
    "silicon_RSoXS":  (1820, 1840, 2.5, 1860, 0.2, 1910, 2.35), ## Intended to recreate edge=(1820,1840,1860,1910), ratios=(2, 0.2, 2), frames=112
    "sulfurL_RSoXS":  (150, 160, 1.25, 170, 0.1, 200, 1.25), ## Intended to recreate edge=(150, 160, 170, 200), ratios=(2, 0.2, 2), frames=112
    "calciumL_RSoXS":  (320, 340, 2.2, 345, 0.45, 349, 0.2, 349.5, 0.05, 352.5, 0.1, 353, 0.05, 355, 0.5, 360, 0.45, 380, 0.2), ## Intended to recreate edge=(320, 340, 345, 349, 349.5, 352.5, 353, 355, 360, 380), ratios=(5, 1, 0.5, 0.1, 0.25, 0.1, 0.5, 1, 5), frames=112
    "ironL_RSoXS":  (680, 700, 3.3, 730, 0.3, 780, 3.3), ## Intended to recreate edge=(680,700,730,780), ratios=(2, 0.2, 2), frames=112
    "zincL_RSoXS":  (1000, 1015, 2.5, 1035, 0.2, 1085, 2.35), ## Intended to recreate edge=(1000, 1015, 1035, 1085), ratios=(2, 0.2, 2), frames=112

    "carbon_NEXAFS_WSU":  (270, 278, 1, 283, 0.5, 291.5, 0.05, 300, 0.5, 330, 1, 350, 4), ## WSU NEXAFS for Brian Collins group
}

#energies_eliot = get_energies(edge=[380, 397, 407, 440], ratios=[2, 0.2, 2], frames=112)
