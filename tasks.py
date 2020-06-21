from invoke import task


@task
def test(ctx):
    ctx.run("pipenv run flake8")
    ctx.run("pipenv run mypy fireclass")
    ctx.run("pipenv run black -l 120 --check fireclass tests sample.py tasks.py")
    ctx.run("pipenv run pytest --cov=fireclass --cov-fail-under 80")
