FROM auth-service-base-img

COPY ci/test_requirements.txt test_requirements.txt
COPY ci/pylintrc pylintrc
COPY tests tests/

RUN pip install -r test_requirements.txt