echo "Running TrackInsights code compliance check"

echo "Running auto-formatters"

conda run -n track-insights isort track_insights > /dev/null
conda run -n track-insights autopep8 track_insights --recursive --in-place --pep8-passes 2000 > /dev/null
conda run -n track-insights black track_insights --verbose --config black_config.toml > /dev/null

echo "Running linters"

if conda run -n track-insights flake8 track_insights ; then
    echo "No flake8 errors"
else
    echo "flake8 errors"
    exit 1
fi

if conda run -n track-insights isort track_insights --check --diff ; then
    echo "No isort errors"
else
    echo "isort errors"
    exit 1
fi

if conda run -n track-insights black --check track_insights --config black_config.toml ; then
    echo "No black errors"
else
    echo "black errors"
    exit 1
fi

if conda run -n track-insights pylint track_insights ; then
    echo "No pylint errors"
else
    echo "pylint errors"
    exit 1
fi

echo "Running tests"

if conda run -n track-insights pytest ; then
    echo "No pytest errors"
else
    echo "pytest errors"
    exit 1
fi

if conda run -n track-insights mypy track_insights ; then
    echo "No mypy errors"
else
    echo "mypy errors"
    exit 1
fi

echo "Successful code compliance check"
