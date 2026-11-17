# Worked example: M/M/1 queue guide

Reproduce the PDF from the original code (run from this folder, SK = the skill folder):

```bash
python $SK/scripts/code_parser.py mm1_queue.py --write-markers mm1_queue_marked_auto.py   # proposes markers
# mm1_queue_marked.py is the hand-refined version (titles edited, long blocks split)
python $SK/scripts/code_parser.py mm1_queue_marked.py --json mm1_queue.analysis.json
python $SK/scripts/run_and_capture.py mm1_queue_marked.py --out run_out
python make_guide.py                                   # -> MM1_Queue_Guide.pdf
python $SK/scripts/render_check.py MM1_Queue_Guide.pdf --out qa
python $SK/scripts/make_notebook.py mm1_queue_marked.py mm1_queue.ipynb --title "M/M/1 Queue"
```
