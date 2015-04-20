@REM extrait les chaines à traduire
@REM --sort-output         generate sorted output (default False)
@REM --sort-by-file        sort output by file location (default False)
@REM --version=VERSION     set project version in output
pybabel extract -F babel\babel.cfg -k gettext -k _gettext -k _ngettext -k lazy_gettext -k _ -o babel\mmw.pot --project Mongo-Mail-Web mongo_mail_web

@REM créé un fichier pour traduire en Français
@REM pybabel init -i babel\mmw.pot -d mongo_mail_web\translations -l fr

@REM met à jour les nouvelles chaines
pybabel update -i babel\mmw.pot -d mongo_mail_web\translations

@REM compile les fichiers de traductions
@REM dans les .po, enlever la chaine #, fuzzy avant de compiler
@REM -l LOCALE, --locale=LOCALE
@REM -f, --use-fuzzy 
pybabel compile -d mongo_mail_web\translations --statistics

