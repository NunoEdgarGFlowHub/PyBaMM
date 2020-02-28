from pybamm import exp


def nco_electrolyte_reaction_rate_Ecker2015(T, T_inf, E_r, R_g):
    """
    Reaction rate for Butler-Volmer reactions between NCO and LiPF6 in EC:DMC [1, 2].

    References
    ----------
       .. [1] Ecker, Madeleine, et al. "Parameterization of a physico-chemical model of
    a lithium-ion battery i. determination of parameters." Journal of the
    Electrochemical Society 162.9 (2015): A1836-A1848.
    .. [2] Ecker, Madeleine, et al. "Parameterization of a physico-chemical model of
    a lithium-ion battery ii. model validation." Journal of The Electrochemical
    Society 162.9 (2015): A1849-A1857.

    Parameters
    ----------
    T: :class: `numpy.Array`
        Dimensional temperature
    T_inf: double
        Reference temperature
    E_r: double
        Reaction activation energy
    R_g: double
        The ideal gas constant

    Returns
    -------
    : double
        Reaction rate
    """

    F = 96487
    k_ref = 5.196e-11
    m_ref = F * k_ref
    arrhenius = exp(-E_r / (R_g * T)) * exp(E_r / (R_g * 296))

    return m_ref * arrhenius
