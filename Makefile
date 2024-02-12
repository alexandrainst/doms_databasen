test:
	pytest tests/scraper && \
	pytest tests/processor
format:
	isort .
	black .
	