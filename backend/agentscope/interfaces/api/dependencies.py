"""
Point de composition unique (ports <-> implémentations <-> config) — I4.10.

Vide pour I4.1 : les routes stub lisent des fixtures statiques et n'ont
besoin d'aucune dépendance injectée. Quand les use cases réels arrivent
(EPIC 1/2/3), chaque route les recevra ici via `Depends(...)`, jamais en
important directement `infrastructure/`.
"""
