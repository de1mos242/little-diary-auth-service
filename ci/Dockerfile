FROM auth-service-base-img

COPY test_requirements.txt test_requirements.txt
COPY pylintrc pylintrc
COPY tests tests/

RUN pip install -r test_requirements.txt