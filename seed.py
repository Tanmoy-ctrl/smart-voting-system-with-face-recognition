# seed.py
from models import init_db, get_session, Candidate
engine = init_db('sqlite:///voting.db')
session = get_session(engine)

# Add candidates if none exist
if session.query(Candidate).count() == 0:
    c1 = Candidate(name='Alice Kumar', party='Party A')
    c2 = Candidate(name='Ravi Singh', party='Party B')
    session.add_all([c1,c2])
    session.commit()
    print("Seeded candidates.")
else:
    print("Candidates already present.")
