# Listes LDNOOBW

`fr.txt` et `en.txt` viennent de **List of Dirty, Naughty, Obscene, and Otherwise Bad Words**
(Shutterstock), https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words

- Licence : Creative Commons Attribution 4.0 (CC-BY-4.0), voir `LICENSE`.
- Récupérées le 2026-11-14 (dernier commit du dépôt : août 2024).
- Les fichiers ne sont pas modifiés. Les mots à double sens (« gerbe », « tanche », « cock »,
  « cum laude »…), les termes médicaux et les jurons très courants sont écartés dans le code :
  voir `EXCLUSIONS_LDNOOBW` dans `abus.py`.

Pour mettre à jour :

```bash
B=https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master
curl -o data/ldnoobw/fr.txt $B/fr && curl -o data/ldnoobw/en.txt $B/en
```
