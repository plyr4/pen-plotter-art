PYTHON := python3
VENV   := venv
PIP    := $(VENV)/bin/pip
RUN    := $(VENV)/bin/python

SKETCH_NAME := $(filter-out run new,$(MAKECMDGOALS))

.PHONY: install run new $(SKETCH_NAME)

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(RUN) main.py run $(if $(SKETCH_NAME),--art $(SKETCH_NAME),) $(if $(CONFIG),--config $(CONFIG),)

new:
	$(RUN) main.py new $(if $(SKETCH_NAME),$(SKETCH_NAME),)

%:
	@:
