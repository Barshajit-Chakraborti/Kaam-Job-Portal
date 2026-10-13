"""Choice lists shared by accounts and jobs."""

EDUCATION_LEVELS = [
    ("12th", "Higher secondary (12th)"),
    ("diploma", "Diploma"),
    ("bachelors", "Bachelor's (B.Tech / B.E. / B.Sc / BCA ...)"),
    ("masters", "Master's (M.Tech / MCA / MBA ...)"),
    ("phd", "PhD"),
]

# Higher number = higher qualification. Used for "at least this level" filtering.
EDUCATION_RANK = {"12th": 1, "diploma": 2, "bachelors": 3, "masters": 4, "phd": 5}

WORK_PREFERENCES = [
    ("remote", "Remote"),
    ("onsite", "Onsite"),
    ("both", "Open to both"),
]
