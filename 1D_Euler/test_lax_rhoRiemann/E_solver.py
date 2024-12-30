import numpy as np
import matplotlib.pyplot as plt

def _pressure_function(p, uu, gamma):
    '''
    Helper function, computing f_l(p,W_k), df_l(p,W_k)
    :param p: pressure
    :param uu: primitive state variables
    :param eos: equation of state
    :return:
    '''
    [rho_k, v_k, p_k] = uu
    if (p > p_k):  # shock

        A_k, B_k = 2 / ((gamma + 1) * rho_k), (gamma - 1) / (gamma + 1) * p_k

        f = (p - p_k) * np.sqrt(A_k / (p + B_k))

        df = np.sqrt(A_k / (B_k + p)) * (1 - (p - p_k) / (2 * (B_k + p)))

    else:  # rarefaction
        a_k = np.sqrt(gamma * p_k / rho_k)

        f = 2 * a_k / (gamma - 1) * ((p / p_k) **
                                     ((gamma - 1) / (2 * gamma)) - 1)

        df = 1 / (rho_k * a_k) * (p / p_k) ** (- (gamma + 1) / (2 * gamma))

    return f, df


def _pressure_function_init(uu_l, uu_r, gamma):
    '''
    guess the initial value of pressure at contact discontinuity
    :param uu_l: left state primitive variables
    :param uu_r: right state primitive variables
    :param gamma: equation of state

    '''
    [rho_l, v_l, p_l] = uu_l

    [rho_r, v_r, p_r] = uu_r

    return 0.5 * (p_l + p_r)


def _solve_contact_discontinuity(uu_l, uu_r, gamma):
    '''
    solve function f(p,W_l,W_r) = f_l(p,W_l) + f_r(p,w_r) + delta v
    :param p: pressure guess at contact discontinuity
    :param uu_l: left state primitive variables
    :param uu_r: right state primitive variables
    :param eos: equation of state
    :return: p,v around the contact discontinuity
    '''

    [rho_l, v_l, p_l] = uu_l
    [rho_r, v_r, p_r] = uu_r

    d_v = v_r - v_l

    MAX_ITE = 100
    TOLERANCE = 1.0e-12
    found = False

    p_old = _pressure_function_init(uu_l, uu_r, gamma)

    for i in range(MAX_ITE):
        f_l, df_l = _pressure_function(p_old, uu_l, gamma)
        f_r, df_r = _pressure_function(p_old, uu_r, gamma)

        p = p_old - (f_l + f_r + d_v) / (df_l + df_r)

        if(p < 0.0):
            p = TOLERANCE

        if (2 * abs(p - p_old) / (p + p_old) < TOLERANCE):
            found = True
            break
        p_old = p

    if not found:
        print('Divergence in Newton-Raphason iteration')

    v = 0.5 * (v_l + v_r + f_r - f_l)

    return p, v


def _sample_solution(p_m, v_m, uu_l, uu_r, gamma, s):
    '''
    :param p: pressure at contact discontinuity
    :param v: velocity at contact discontinuity
    :param uu_l: left primitive variables
    :param uu_r: right primitive variables
    :param gamma: equation of state
    :param s: sample point satisfies s = x/t
    :return: rho, v , p at (t,x)
    '''

    [rho_l, v_l, p_l] = uu_l
    a_l = np.sqrt(gamma * p_l / rho_l)

    [rho_r, v_r, p_r] = uu_r
    a_r = np.sqrt(gamma * p_r / rho_r)

    if s < v_m:
        # sampling point lies to the left of the contact discontinuity
        if p_m < p_l:

            # left rarefaction
            s_l = v_l - a_l
            a_ml = a_l * (p_m / p_l) ** ((gamma - 1) / (2 * gamma))
            s_ml = v_m - a_ml
            if s < s_l:  # left state
                rho, v, p = rho_l, v_l, p_l

            elif s < s_ml:  # left rarefaction wave
                rho = rho_l * (2 / (gamma + 1) + (gamma - 1) /
                               ((gamma + 1) * a_l) * (v_l - s)) ** (2 / (gamma - 1))
                v = 2 / (gamma + 1) * (a_l + (gamma - 1) / 2.0 * v_l + s)
                p = p_l * (2 / (gamma + 1) + (gamma - 1) / ((gamma + 1)
                                                            * a_l) * (v_l - s)) ** (2 * gamma / (gamma - 1))

            else:  # left contact discontinuity
                rho, v, p = rho_l * (p_m / p_l) ** (1 / gamma), v_m, p_m
        else:
            # left shock

            s_shock = v_l - a_l * \
                np.sqrt((gamma + 1) * p_m / (2 * gamma * p_l) +
                        (gamma - 1) / (2 * gamma))

            if s < s_shock:
                rho, v, p = rho_l, v_l, p_l
            else:
                rho = rho_l * (p_m / p_l + (gamma - 1) / (gamma + 1)) / \
                    ((gamma - 1) * p_m / ((gamma + 1) * p_l) + 1)
                v = v_m
                p = p_m
    else:
        # sampling point lies to the right of the contact discontinuity

        if p_m < p_r:

            # right rarefaction
            s_r = v_r + a_r
            a_mr = a_r * (p_m / p_r) ** ((gamma - 1) / (2 * gamma))
            s_mr = v_m + a_mr
            if s > s_r:  # left state
                rho, v, p = rho_r, v_r, p_r

            elif s > s_mr:  # left rarefaction wave
                rho = rho_r * (2 / (gamma + 1) - (gamma - 1) /
                               ((gamma + 1) * a_r) * (v_r - s)) ** (2 / (gamma - 1))
                v = 2 / (gamma + 1) * (-a_r + (gamma - 1) / 2.0 * v_r + s)
                p = p_r * (2 / (gamma + 1) - (gamma - 1) / ((gamma + 1)
                                                            * a_r) * (v_r - s)) ** (2 * gamma / (gamma - 1))

            else:  # left contact discontinuity
                rho, v, p = rho_r * (p_m / p_r) ** (1/gamma), v_m, p_m
        else:
            # right shock

            s_shock = v_r + a_r * \
                np.sqrt((gamma + 1) * p_m / (2 * gamma * p_r) +
                        (gamma - 1) / (2 * gamma))

            if s > s_shock:  # after shock
                rho, v, p = rho_r, v_r, p_r
            else:
                # preshock, contact discontinuity
                rho = rho_r * (p_m / p_r + (gamma - 1) / (gamma + 1)) / \
                    ((gamma - 1) * p_m / ((gamma + 1) * p_r) + 1)
                v = v_m
                p = p_m
    return rho, p, v

def exact_solver(uu_l, uu_r, gamma, t, N):
    # draw the solution
    L = 1  # _compute_domain(uu_l, uu_r, gamma, t)
    x = np.linspace(-L/2, L/2, num=N)

    uu = np.empty([N, 3], dtype=float)

    p_m, v_m = _solve_contact_discontinuity(uu_l, uu_r, gamma)

    for i in range(N):
        uu[i, :] = _sample_solution(p_m, v_m, uu_l, uu_r, gamma, x[i] / t)
    uu = np.hstack((uu, np.linspace(0, 1, num=N).reshape(N,1)))
    '''
    plt.style.use("ggplot") 
    plt.plot(np.linspace(0, L, num=N), uu[:, 0], '-b',label ='Density')
    plt.plot(np.linspace(0, L, num=N), uu[:, 1], '-r',label = 'Velocity')
    plt.plot(np.linspace(0, L, num=N), uu[:, 2], '-g',label ='Pressure')
    plt.title(f'$\gamma$ = {gamma}')
    plt.legend()
    plt.show()
    '''
    return uu[:,:1],uu[:,1:2],uu[:,2:3],uu[:,3:]