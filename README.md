<h1>0c1</h1>

0c1 is a script that goes through PDF content(s) and calls OpenAI to prepare data for fine-tuning of another data set.

Simply create .env file, add your OpenAI Api, then load content to the sources_data_3 folder (don't forget to change it in the script if you want to have it named differently, I was lazy), review the prompt on line 44 and then run it.

The prompt on line 44 is built for financial books and for question/answer style. Don't forget to change the topic otherwise, you'll get skewed outcomes.

The script will create file called output_dataset.jsonl which you can then use for training of your own models.
