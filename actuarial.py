"""
ActuarialFleet — motore attuariale
GLM, credibilità Bühlmann-Straub, Chain Ladder, tariffazione
"""
import numpy as np
import pandas as pd

# ── DATI PROVINCE ──
PROVINCE = {
    "RE": {"nome": "Reggio Emilia",    "zona": 3, "imp": 0.16,  "freq": 0.085, "furt": 0.0025, "rec": 0.70, "finc": 0.00025, "srca": 2650, "sfurt": 5400,  "sinc": 7200},
    "CE": {"nome": "Caserta",          "zona": 1, "imp": 0.16,  "freq": 0.145, "furt": 0.028,  "rec": 0.30, "finc": 0.00060, "srca": 3100, "sfurt": 12600, "sinc": 9900},
    "BO": {"nome": "Bologna",          "zona": 2, "imp": 0.16,  "freq": 0.110, "furt": 0.004,  "rec": 0.65, "finc": 0.00030, "srca": 2800, "sfurt": 6000,  "sinc": 7500},
    "MI": {"nome": "Milano",           "zona": 2, "imp": 0.16,  "freq": 0.115, "furt": 0.006,  "rec": 0.60, "finc": 0.00040, "srca": 2900, "sfurt": 7200,  "sinc": 8000},
    "NA": {"nome": "Napoli",           "zona": 1, "imp": 0.16,  "freq": 0.160, "furt": 0.035,  "rec": 0.25, "finc": 0.00080, "srca": 3200, "sfurt": 14000, "sinc": 10500},
    "RM": {"nome": "Roma",             "zona": 2, "imp": 0.16,  "freq": 0.120, "furt": 0.008,  "rec": 0.55, "finc": 0.00045, "srca": 2950, "sfurt": 8000,  "sinc": 8200},
    "TO": {"nome": "Torino",           "zona": 2, "imp": 0.16,  "freq": 0.100, "furt": 0.005,  "rec": 0.62, "finc": 0.00035, "srca": 2750, "sfurt": 6500,  "sinc": 7600},
    "FI": {"nome": "Firenze",          "zona": 2, "imp": 0.16,  "freq": 0.105, "furt": 0.004,  "rec": 0.63, "finc": 0.00030, "srca": 2780, "sfurt": 6200,  "sinc": 7400},
    "PA": {"nome": "Palermo",          "zona": 1, "imp": 0.16,  "freq": 0.155, "furt": 0.030,  "rec": 0.28, "finc": 0.00070, "srca": 3050, "sfurt": 13000, "sinc": 10000},
    "BA": {"nome": "Bari",             "zona": 1, "imp": 0.16,  "freq": 0.140, "furt": 0.022,  "rec": 0.32, "finc": 0.00065, "srca": 3000, "sfurt": 11500, "sinc": 9800},
    "RC": {"nome": "Reggio Calabria",  "zona": 1, "imp": 0.16,  "freq": 0.165, "furt": 0.032,  "rec": 0.25, "finc": 0.00075, "srca": 3150, "sfurt": 13500, "sinc": 10200},
    "CT": {"nome": "Catania",          "zona": 1, "imp": 0.16,  "freq": 0.150, "furt": 0.028,  "rec": 0.28, "finc": 0.00070, "srca": 3080, "sfurt": 12800, "sinc": 10100},
    "SA": {"nome": "Salerno",          "zona": 1, "imp": 0.16,  "freq": 0.145, "furt": 0.025,  "rec": 0.30, "finc": 0.00065, "srca": 3050, "sfurt": 12000, "sinc": 9900},
    "GE": {"nome": "Genova",           "zona": 2, "imp": 0.16,  "freq": 0.108, "furt": 0.006,  "rec": 0.58, "finc": 0.00040, "srca": 2820, "sfurt": 7000,  "sinc": 7800},
    "VE": {"nome": "Venezia",          "zona": 3, "imp": 0.14,  "freq": 0.080, "furt": 0.003,  "rec": 0.68, "finc": 0.00022, "srca": 2580, "sfurt": 5200,  "sinc": 7100},
    "PD": {"nome": "Padova",           "zona": 3, "imp": 0.14,  "freq": 0.082, "furt": 0.003,  "rec": 0.67, "finc": 0.00023, "srca": 2600, "sfurt": 5300,  "sinc": 7100},
    "VR": {"nome": "Verona",           "zona": 3, "imp": 0.14,  "freq": 0.078, "furt": 0.0028, "rec": 0.69, "finc": 0.00020, "srca": 2570, "sfurt": 5100,  "sinc": 7000},
    "BS": {"nome": "Brescia",          "zona": 3, "imp": 0.15,  "freq": 0.090, "furt": 0.0035, "rec": 0.66, "finc": 0.00028, "srca": 2650, "sfurt": 5500,  "sinc": 7200},
    "MN": {"nome": "Mantova",          "zona": 3, "imp": 0.13,  "freq": 0.070, "furt": 0.002,  "rec": 0.72, "finc": 0.00018, "srca": 2500, "sfurt": 4800,  "sinc": 6800},
    "BZ": {"nome": "Bolzano",          "zona": 4, "imp": 0.09,  "freq": 0.045, "furt": 0.0008, "rec": 0.80, "finc": 0.00010, "srca": 2200, "sfurt": 3500,  "sinc": 5500},
    "TN": {"nome": "Trento",           "zona": 4, "imp": 0.10,  "freq": 0.050, "furt": 0.001,  "rec": 0.78, "finc": 0.00012, "srca": 2250, "sfurt": 3800,  "sinc": 5700},
    "AO": {"nome": "Aosta",            "zona": 4, "imp": 0.09,  "freq": 0.042, "furt": 0.0007, "rec": 0.82, "finc": 0.00009, "srca": 2150, "sfurt": 3200,  "sinc": 5300},
    "GEN": {"nome": "Altra provincia", "zona": 3, "imp": 0.125, "freq": 0.085, "furt": 0.003,  "rec": 0.65, "finc": 0.00025, "srca": 2600, "sfurt": 5000,  "sinc": 7000},
}

CIL_MAP   = {"bassa": 0.80, "media": 1.00, "alta": 1.25, "sportiva": 2.00}
USO_MAP   = {"svago": 0.85, "promiscuo": 1.00, "lavoro": 1.20}
BM_MAP    = {"Classe 1": 0.50, "Classe 4": 0.75, "Classe 7": 1.00, "Classe 12": 1.35, "Classe 18": 1.80}

def get_prov(codice: str) -> dict:
    return PROVINCE.get(codice.upper(), PROVINCE["GEN"])

# ── FRANCHIGIA / SCOPERTO ──
def quota_ass(danno, franc=0, scop_pct=0, scop_min=0, scop_max=np.inf):
    if franc == 0 and scop_pct == 0:
        return 0.0
    q_franc = franc
    q_scop  = max(danno * scop_pct, scop_min) if scop_pct > 0 else 0
    if np.isfinite(scop_max):
        q_scop = min(q_scop, scop_max)
    return max(q_franc, q_scop)

def risparmio_franchigia(freq, sev_media, franc=0, scop_pct=0, scop_min=0, scop_max=np.inf):
    q = quota_ass(sev_media, franc, scop_pct, scop_min, scop_max)
    return freq * min(q, sev_media)

# ── TARIFFAZIONE RCA ──
def calcola_premio(
    prov_code: str,
    nveic: int = 200,
    cil: float = 1.0,
    bm: float = 1.0,
    uso: float = 1.0,
    sconto_fleet: float = 0.08,
    rca_franc: float = 0.0,
    rca_scop_pct: float = 0.0,
    rca_scop_min: float = 0.0,
    rca_scop_max: float = np.inf,
    mass_pers: float = 10_000_000,
    valore_assicurato: float = 18_000,
    sval_pct: float = 0.15,
    anni_vet: int = 3,
    furto: bool = True,
    franc_furto: float = 500,
    scop_furto_pct: float = 0.15,
    scop_furto_min: float = 400,
    gps: bool = True,
    incendio: bool = True,
    franc_inc: float = 500,
    scop_inc_pct: float = 0.15,
    kasko: bool = False,
    scop_kasko_pct: float = 0.10,
    scop_kasko_min: float = 500,
    mass_kasko: float = 20_000,
    infortuni: bool = False,
    premio_infortuni: float = 20.0,
) -> dict:
    p = get_prov(prov_code)

    # Massimale adj
    mass_adj = 1 + max(0, mass_pers / 1e6 - 6.07) * 0.003

    # RCA puro
    mult   = cil * bm * uso
    pp_base = 200 * mult
    risp   = risparmio_franchigia(p["freq"], p["srca"], rca_franc, rca_scop_pct, rca_scop_min, rca_scop_max)
    pp_adj  = max(pp_base - risp, pp_base * 0.3) * mass_adj
    lae    = pp_adj * 0.08
    spese  = pp_adj * 0.18
    margine = pp_adj * 0.05 + 12.5
    pre_sc  = pp_adj + lae + spese + margine
    netto  = pre_sc * (1 - sconto_fleet)
    ssn    = netto * 0.105
    sub    = netto + ssn
    imp    = sub * p["imp"]
    lordo_rca = sub + imp

    # Valore svalutato
    val_s = valore_assicurato * (1 - sval_pct) ** anni_vet

    # Furto
    pp_furto = lordo_furto = 0.0
    if furto:
        sev_f = val_s * (1 - p["rec"])
        r_f   = risparmio_franchigia(p["furt"], sev_f, franc_furto, scop_furto_pct, scop_furto_min)
        pp_furto = max(p["furt"] * sev_f * 1.26 * 1.05 * 0.92 - r_f, p["furt"] * sev_f * 0.10)
        if gps:
            pp_furto *= 0.85
        lordo_furto = pp_furto * 1.125

    # Incendio
    pp_inc = lordo_inc = 0.0
    if incendio:
        sev_i = val_s * 0.45
        r_i   = risparmio_franchigia(p["finc"], sev_i, franc_inc, scop_inc_pct, 0)
        pp_inc = max(p["finc"] * sev_i * 1.26 * 1.05 * 0.92 - r_i, p["finc"] * sev_i * 0.10)
        lordo_inc = pp_inc * 1.125

    # Kasko
    pp_kasko = lordo_kasko = 0.0
    if kasko:
        fq_k  = p["freq"] * 1.5
        sev_k = min(val_s * 0.25, mass_kasko)
        r_k   = risparmio_franchigia(fq_k, sev_k, 0, scop_kasko_pct, scop_kasko_min, mass_kasko)
        pp_kasko = max(fq_k * sev_k * 1.26 * 1.05 * 0.92 - r_k, fq_k * sev_k * 0.15)
        lordo_kasko = pp_kasko * 1.125

    # Infortuni
    lordo_infort = premio_infortuni * 1.125 if infortuni else 0.0

    lordo_tot = lordo_rca + lordo_furto + lordo_inc + lordo_kasko + lordo_infort
    quota_flotta = quota_ass(p["srca"], rca_franc, rca_scop_pct, rca_scop_min, rca_scop_max) * p["freq"] * nveic

    return {
        "prov":         p,
        "mult":         mult,
        "pp_base":      pp_base,
        "risp_franc":   risp,
        "pp_adj":       pp_adj,
        "val_sval":     val_s,
        "netto":        netto,
        "ssn":          ssn,
        "imp_prov":     imp,
        "lordo_rca":    lordo_rca,
        "pp_furto":     pp_furto,
        "lordo_furto":  lordo_furto,
        "pp_inc":       pp_inc,
        "lordo_inc":    lordo_inc,
        "pp_kasko":     pp_kasko,
        "lordo_kasko":  lordo_kasko,
        "lordo_infort": lordo_infort,
        "lordo_tot":    lordo_tot,
        "lordo_fleet":  lordo_tot * nveic,
        "quota_flotta": quota_flotta,
        "sin_attesi":   p["freq"] * nveic,
        "mass_adj":     mass_adj,
    }

# ── GLM (statsmodels) ──
def glm_frequenza(df: pd.DataFrame, target_col="n_sinistri", exp_col="esposizione"):
    """Stima GLM Poisson su dati reali se disponibili."""
    try:
        import statsmodels.api as sm
        X = df.drop(columns=[target_col, exp_col], errors="ignore")
        X = pd.get_dummies(X, drop_first=True)
        X = sm.add_constant(X.astype(float))
        y = df[target_col].astype(float)
        exposure = df[exp_col].astype(float) if exp_col in df.columns else None
        model = sm.GLM(y, X, family=sm.families.Poisson(),
                       exposure=exposure if exposure is not None else None)
        result = model.fit()
        return result
    except Exception as e:
        return None

def glm_parametrico(freq=0.085, kappa=8, sev=2650, cov=0.72, is_nb=False):
    """Calcolo parametrico per la UI (no dati richiesti)."""
    pp   = freq * sev
    var_N = (freq + freq**2 / kappa) if is_nb else freq
    var_S = freq * (cov * sev)**2 + sev**2 * var_N
    sd_S  = np.sqrt(var_S)
    alpha = 1 / cov**2
    od    = (1 + freq / kappa) if is_nb else 1.0
    return {
        "pp": pp, "sd": sd_S, "alpha": alpha,
        "od": od, "var_95": pp + 1.645 * sd_S,
        "var_99_5": pp + 2.807 * sd_S,
        "cov_comp": sd_S / pp * 100,
    }

# ── CREDIBILITÀ BÜHLMANN-STRAUB ──
def credibilita(lcoll, exp_veic, anni, lobs, var_b, mu_fleet, mu_coll=2600):
    var_w = lcoll
    k     = var_w / var_b
    n     = exp_veic * anni
    Z     = n / (n + k)
    lstar = Z * lobs + (1 - Z) * lcoll
    mu_star = Z * mu_fleet + (1 - Z) * mu_coll
    pp_star  = lstar * mu_star
    delta    = (lstar / lcoll - 1) * 100
    return {
        "k": k, "n": n, "Z": Z, "lstar": lstar,
        "mu_star": mu_star, "pp_star": pp_star, "delta": delta,
    }

# ── CHAIN LADDER ──
def chain_ladder(triangle: list) -> dict:
    n = len(triangle)
    obs  = [list(r) for r in triangle]
    ldfs = []
    for d in range(n - 1):
        num = den = 0
        for y in range(n - d - 1):
            if obs[y][d] is not None and obs[y][d + 1] is not None:
                den += obs[y][d]
                num += obs[y][d + 1]
        ldfs.append(num / den if den > 0 else 1.0)

    cdfs = []
    cum  = 1.0
    for ldf in reversed(ldfs):
        cum *= ldf
        cdfs.insert(0, cum)
    cdfs.append(1.0)

    full = [list(r) for r in obs]
    for y in range(n):
        for d in range(n):
            if full[y][d] is None and d > 0 and full[y][d - 1] is not None and d - 1 < len(ldfs):
                full[y][d] = round(full[y][d - 1] * ldfs[d - 1])

    ibnr_rows = []
    total_ibnr = 0
    years = list(range(2019, 2019 + n))
    for y in range(n):
        ult  = full[y][n - 1]
        paid = next((v for v in reversed(obs[y]) if v is not None), ult)
        ibnr = max(ult - paid, 0)
        total_ibnr += ibnr
        ibnr_rows.append({"anno": years[y], "ultimate": ult, "pagato": paid, "ibnr": ibnr})

    return {
        "full": full, "ldfs": ldfs, "cdfs": cdfs,
        "ibnr_rows": ibnr_rows, "total_ibnr": total_ibnr,
        "years": years,
    }

DEFAULT_TRIANGLE = [
    [1200, 1560, 1680, 1720, 1740],
    [1350, 1750, 1890, 1930, None],
    [1100, 1430, 1540, None, None],
    [1420, 1850, None, None, None],
    [1600, None, None, None, None],
]
