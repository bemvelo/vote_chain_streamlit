import streamlit as st
import hashlib
import time
import uuid
import threading
from collections import Counter

# -------------------------
# Blockchain Classes
# -------------------------
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def proof_of_work(self, difficulty=2):
        prefix = '0' * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.compute_hash()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.lock = threading.Lock()
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), "Genesis Block", "0")
        self.chain.append(genesis_block)

    def add_block(self, data):
        with self.lock:
            last_block = self.chain[-1]
            new_block = Block(len(self.chain), time.time(), data, last_block.hash)
            new_block.proof_of_work()
            self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.hash != curr.compute_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
        return True


# -------------------------
# Voting System Classes
# -------------------------
class User:
    def __init__(self, name):
        self.name = name
        self.voter_id = None

class IDVerifier:
    def verify_user(self, user):
        user.voter_id = str(uuid.uuid4())
        return user.voter_id

class Registrar:
    def __init__(self):
        self.authorized_voters = set()
        self.voted_voters = set()

    def authorize(self, user):
        if user.voter_id:
            self.authorized_voters.add(user.voter_id)
            return True
        return False

    def is_authorized(self, voter_id):
        return voter_id in self.authorized_voters and voter_id not in self.voted_voters

    def mark_voted(self, voter_id):
        self.voted_voters.add(voter_id)

class Ballot:
    def __init__(self, voter_id, candidate):
        self.voter_id = voter_id
        self.candidate = candidate


# -------------------------
# Initialize System
# -------------------------
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
if 'verifier' not in st.session_state:
    st.session_state.verifier = IDVerifier()
if 'registrar' not in st.session_state:
    st.session_state.registrar = Registrar()
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'candidates' not in st.session_state:
    st.session_state.candidates = {}


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Blockchain Voting System", layout="wide")
st.title("🗳️ Blockchain-Based Voting System")

menu = st.sidebar.radio("Navigation", ["Register Voter", "Register Candidate", "Vote", "View Votes", "View Blockchain"])

blockchain = st.session_state.blockchain
registrar = st.session_state.registrar
verifier = st.session_state.verifier
users = st.session_state.users
candidates = st.session_state.candidates


# -------------------------
# Register Voter Page
# -------------------------
if menu == "Register Voter":
    st.header("👤 Register a New Voter")
    name = st.text_input("Enter your name:")
    if st.button("Register Voter"):
        if name:
            user = User(name)
            verifier.verify_user(user)
            registrar.authorize(user)
            users[user.voter_id] = user
            st.success(f"✅ Voter Registered! Your Voter ID: {user.voter_id}")
        else:
            st.warning("Please enter your name.")


# -------------------------
# Register Candidate Page
# -------------------------
elif menu == "Register Candidate":
    st.header("🏛️ Register a Candidate")
    cname = st.text_input("Candidate Name:")
    if st.button("Add Candidate"):
        if cname:
            cid = str(uuid.uuid4())[:8]
            candidates[cid] = cname
            st.success(f"✅ Candidate '{cname}' registered with ID: {cid}")
        else:
            st.warning("Please enter a candidate name.")

    if candidates:
        st.subheader("📋 Registered Candidates")
        for cid, cname in candidates.items():
            st.write(f"🆔 **{cid}** - {cname}")
    else:
        st.info("No candidates registered yet.")


# -------------------------
# Vote Page
# -------------------------
elif menu == "Vote":
    st.header("🗳️ Cast Your Vote")
    voter_id = st.text_input("Enter your Voter ID:")

    if not candidates:
        st.warning("No candidates available. Please register candidates first.")
    else:
        if voter_id:
            if voter_id not in users:
                st.error("Voter not found! Please register first.")
            elif not registrar.is_authorized(voter_id):
                st.error("Unauthorized or already voted!")
            else:
                candidate_name = st.selectbox("Select Candidate", list(candidates.values()))
                if st.button("Submit Vote"):
                    ballot = Ballot(voter_id, candidate_name)
                    blockchain.add_block(vars(ballot))
                    registrar.mark_voted(voter_id)
                    st.success(f"✅ Vote cast successfully for {candidate_name}")
        else:
            st.info("Enter your voter ID to vote.")


# -------------------------
# View Votes Page
# -------------------------
elif menu == "View Votes":
    st.header("📊 Voting Results")

    votes = []
    for block in blockchain.chain[1:]:  # skip genesis block
        data = block.data
        if isinstance(data, dict) and "candidate" in data:
            votes.append(data["candidate"])

    if votes:
        vote_counts = Counter(votes)
        st.bar_chart(vote_counts)
        st.subheader("Vote Tally")
        for candidate, count in vote_counts.items():
            st.write(f"🗳️ **{candidate}**: {count} votes")
    else:
        st.info("No votes have been cast yet.")


# -------------------------
# Blockchain Explorer Page
# -------------------------
elif menu == "View Blockchain":
    st.header("🔗 Blockchain Explorer")
    for block in blockchain.chain:
        with st.expander(f"Block {block.index}"):
            st.write({
                "Index": block.index,
                "Timestamp": block.timestamp,
                "Data": block.data,
                "Previous Hash": block.previous_hash,
                "Hash": block.hash,
                "Nonce": block.nonce
            })
