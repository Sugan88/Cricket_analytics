# Tableau workbook

`australia_india_batting.twb` — four sheets on one dashboard:
country averages, phase decay (average and strike rate), dismissal mix.

The workbook references CSVs in `exports/tableau/`, which are not
committed. To open it:

    python scripts/export_for_tableau.py

Then open the .twb. If Tableau prompts for the data source, point it at
`exports/tableau/`.
