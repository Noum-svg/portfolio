import numpy as np

def ajouter_variables_ecart(A, b):
    """Ajoute des variables d'écart pour transformer les inégalités en égalités."""
    m, n = A.shape
    A_ecart = np.hstack((A, np.eye(m)))
    c_ecart = np.hstack((np.zeros(n), np.ones(m)))  # Coût des variables d'écart
    return A_ecart, b, c_ecart

def initialiser_simplexe(A, b, c):
    """Trouve une solution de base admissible initiale."""
    m, n = A.shape
    permut = list(range(n))
    # Ajout des indices des variables d'écart
    permut += list(range(n, n+m))
    return permut

def simplexe(A, b, c):
    A, b, c = ajouter_variables_ecart(A, b)
    permut = initialiser_simplexe(A, b, c)
    m, n = A.shape

    while True:
        # Matrice des variables de base
        B = np.array([A[:, j] for j in permut[:m]]).T

        # Vérifier si la matrice de base est inversible
        if np.linalg.det(B) == 0:
            return None, 'La matrice de base n\'est pas inversible'

        # Calculer la solution de base
        x_b = np.linalg.solve(B, b)

        # Coûts réduits
        c_b = c[permut[:m]]
        y = np.linalg.solve(B.T, c_b)
        c_n = c[permut[m:]]
        A_n = A[:, permut[m:]]
        coûts_réduits = c_n - np.dot(y.T, A_n)

        # Vérifier l'optimalité
        if all(coût >= 0 for coût in coûts_réduits):
            x = np.zeros(n)
            x[permut[:m]] = x_b
            return x, np.dot(c, x), 'Solution optimale trouvée'

        # Variable entrante (celle avec le coût réduit le plus négatif)
        j_n = np.argmin(coûts_réduits)
        variable_entrante = permut[m + j_n]

        # Direction de recherche
        d = np.linalg.solve(B, A[:, variable_entrante])

        # Vérifier l'illimité
        if all(d_i <= 0 for d_i in d):
            return None, 'La solution est illimitée'

        # Variable sortante
        rapports = [x_b[i] / d[i] if d[i] > 0 else np.inf for i in range(m)]
        i_sortante = np.argmin(rapports)
        variable_sortante = permut[i_sortante]

        # Mise à jour de la permutation
        permut[i_sortante], permut[m + j_n] = permut[m + j_n], permut[i_sortante]

