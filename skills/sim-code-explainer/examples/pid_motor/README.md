# Worked example: DC motor PID guide

Reproduce the PDF from the original code (run from this folder, SK = the skill folder):

```bash
python $SK/scripts/code_parser.py pid_motor.py --write-markers pid_motor_marked_auto.py   # proposes markers
# pid_motor_marked.py is the hand-refined version (titles edited, long blocks split)
python $SK/scripts/code_parser.py pid_motor_marked.py --json pid_motor.analysis.json
python $SK/scripts/run_and_capture.py pid_motor_marked.py --out run_out
python make_guide.py                                   # -> DC_Motor_PID_Guide.pdf
python $SK/scripts/render_check.py DC_Motor_PID_Guide.pdf --out qa
python $SK/scripts/make_notebook.py pid_motor_marked.py pid_motor.ipynb --title "DC Motor PID Speed Control"
```
