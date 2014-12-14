REM Create doc files from .json items, and models from docs 
python readjson.py -i cdc_articles.json -o cdc_docs/docs
python genModel.py -d cdc_docs -i -m cdc_models/articles
python genModel.py -d cdc_docs -a -m cdc_articles 
python rank.py -d cdc_models -c cdc_articles_all.model -o cdc_results/ebola.result --query="ebola"
 