import random
import datetime
import string
from faker import Faker


fake = Faker()
datetime_now = datetime.datetime.now()
newline = '\n'

# Generate data and write to file
with open('Vericelusers.txt', 'w') as f:
    f.write("BOF{}{}{}850{}".format(newline, datetime_now, newline, newline))

    for i in range(100):
        lastname = fake.last_name()
        firstname = fake.first_name()
        job_title = fake.job()
        email = fake.email()
        f.write("{}{}|{}|{}||||{}|||||{}{}".format(
            firstname[0], lastname, lastname, firstname, job_title, email, newline))
