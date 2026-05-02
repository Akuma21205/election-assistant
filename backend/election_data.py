"""
Comprehensive election data for RAG and agent tools.
Covers India, USA, UK with detailed voting processes, timelines, eligibility, and registration.
"""

ELECTION_DATA = {
    "india": {
        "country": "India",
        "voting_age": 18,
        "election_commission": "Election Commission of India (ECI)",
        "website": "https://eci.gov.in",
        "voter_id": "EPIC (Electors Photo Identity Card)",
        "registration": {
            "steps": [
                "Visit the National Voters' Service Portal (NVSP) at voters.eci.gov.in",
                "Click on 'New Voter Registration' (Form 6)",
                "Fill in personal details: name, date of birth, address, constituency",
                "Upload a passport-size photograph and age proof document",
                "Submit the form online or at your nearest Electoral Registration Officer (ERO)",
                "Track your application status using the reference ID",
                "Receive your EPIC (Voter ID card) after verification"
            ],
            "documents_required": [
                "Proof of age (birth certificate, school leaving certificate, passport)",
                "Proof of address (Aadhaar, utility bill, ration card, passport)",
                "Passport-size photographs (recent)"
            ],
            "online_portal": "https://voters.eci.gov.in",
            "form": "Form 6 (for new registration), Form 6B (for Aadhaar linking)",
            "processing_time": "Usually 15-30 days after verification"
        },
        "voting_process": [
            "Check your name on the electoral roll at electoralsearch.eci.gov.in",
            "Find your polling booth location using the Voter Helpline App or website",
            "Visit your designated polling booth on Election Day with valid ID",
            "Join the queue and wait for your turn",
            "The polling officer verifies your identity and marks your finger with indelible ink",
            "Enter the voting compartment and press the button on the EVM next to your preferred candidate",
            "You will hear a beep and see a VVPAT slip confirming your vote",
            "Exit the polling booth after casting your vote"
        ],
        "election_types": [
            {"type": "Lok Sabha (General Elections)", "frequency": "Every 5 years", "description": "Elections to the lower house of Parliament, 543 constituencies"},
            {"type": "Rajya Sabha", "frequency": "Members elected by state legislatures, 1/3 retire every 2 years", "description": "Upper house of Parliament"},
            {"type": "State Assembly (Vidhan Sabha)", "frequency": "Every 5 years", "description": "Elections to state legislative assemblies"},
            {"type": "Local Body Elections", "frequency": "Every 5 years", "description": "Panchayat, Municipal Corporation, Municipality elections"}
        ],
        "timelines": {
            "2024": {
                "Lok Sabha Elections": {
                    "announcement": "March 16, 2024",
                    "phase_1": "April 19, 2024",
                    "phase_2": "April 26, 2024",
                    "phase_3": "May 7, 2024",
                    "phase_4": "May 13, 2024",
                    "phase_5": "May 20, 2024",
                    "phase_6": "May 25, 2024",
                    "phase_7": "June 1, 2024",
                    "results": "June 4, 2024"
                }
            },
            "general_timeline": {
                "Model Code of Conduct": "Begins on date of announcement",
                "Nomination filing": "Usually 7-10 days after announcement",
                "Scrutiny of nominations": "1 day after last date of filing",
                "Last date for withdrawal": "2 days after scrutiny",
                "Polling": "As per schedule",
                "Counting": "Usually within 3-5 days of last phase"
            }
        },
        "eligibility": {
            "age": "Must be 18 years or older on the qualifying date (January 1 of the year of electoral roll revision)",
            "citizenship": "Must be an Indian citizen",
            "residency": "Must be a resident of the constituency where you want to vote",
            "disqualifications": [
                "Non-citizen of India",
                "Of unsound mind (as declared by a competent court)",
                "Disqualified under any law related to corrupt practices or election offenses"
            ]
        },
        "important_contacts": {
            "Voter Helpline": "1950",
            "NVSP Portal": "voters.eci.gov.in",
            "Voter Helpline App": "Available on Google Play and App Store"
        }
    },
    "usa": {
        "country": "United States of America",
        "voting_age": 18,
        "election_commission": "Federal Election Commission (FEC) + State Election Offices",
        "website": "https://www.usa.gov/voting",
        "voter_id": "Varies by state (some require photo ID, some accept non-photo ID)",
        "registration": {
            "steps": [
                "Check if you're already registered at vote.gov",
                "Register online (available in most states), by mail, or in person",
                "Provide your name, address, date of birth, and last 4 digits of SSN",
                "Some states offer same-day registration at polling places",
                "Verify your registration before Election Day",
                "Update your registration if you move or change your name"
            ],
            "documents_required": [
                "State-issued photo ID (driver's license, state ID)",
                "Last 4 digits of Social Security Number",
                "Proof of citizenship (for some states)",
                "Proof of residency (utility bill, bank statement)"
            ],
            "online_portal": "https://vote.gov",
            "deadline": "Varies by state (usually 15-30 days before Election Day)",
            "processing_time": "Usually 2-4 weeks"
        },
        "voting_process": [
            "Verify your voter registration and polling place at vote.gov",
            "Review your sample ballot to know the candidates and ballot measures",
            "Go to your designated polling place on Election Day (or vote early/by mail if available)",
            "Bring required identification (varies by state)",
            "Check in with poll workers who will verify your identity",
            "Receive your ballot (paper or electronic depending on location)",
            "Mark your choices in a private voting booth",
            "Feed your ballot into the scanner or submit electronically",
            "Get your 'I Voted' sticker!"
        ],
        "election_types": [
            {"type": "Presidential Election", "frequency": "Every 4 years", "description": "Elect the President and Vice President via Electoral College"},
            {"type": "Midterm Elections", "frequency": "Every 4 years (between presidential elections)", "description": "All 435 House seats + 1/3 of Senate seats"},
            {"type": "Congressional Elections", "frequency": "Every 2 years", "description": "House of Representatives (all seats) + Senate (1/3)"},
            {"type": "State & Local Elections", "frequency": "Varies", "description": "Governor, state legislature, mayors, school boards, ballot measures"},
            {"type": "Primary Elections", "frequency": "Before general elections", "description": "Party nominations for general election candidates"}
        ],
        "timelines": {
            "2024": {
                "Presidential Election": {
                    "primary_season": "January - June 2024",
                    "party_conventions": "July - August 2024",
                    "general_election": "November 5, 2024",
                    "electoral_vote_count": "January 6, 2025",
                    "inauguration": "January 20, 2025"
                }
            },
            "general_timeline": {
                "Voter registration deadline": "15-30 days before Election Day (varies by state)",
                "Early voting": "Usually starts 10-45 days before Election Day",
                "Mail-in ballot request": "Usually 30-60 days before Election Day",
                "Election Day": "First Tuesday after the first Monday in November",
                "Results": "Usually election night, some states take days"
            }
        },
        "eligibility": {
            "age": "Must be 18 years or older on Election Day",
            "citizenship": "Must be a U.S. citizen",
            "residency": "Must be a resident of the state where you register",
            "disqualifications": [
                "Non-U.S. citizens",
                "Some states: people with felony convictions (varies by state)",
                "People declared mentally incompetent by a court (varies by state)"
            ]
        },
        "electoral_college": {
            "total_votes": 538,
            "to_win": 270,
            "explanation": "Each state gets electoral votes equal to its Congressional representation (House + Senate). Most states use winner-take-all. Maine and Nebraska use congressional district method."
        }
    },
    "uk": {
        "country": "United Kingdom",
        "voting_age": 18,
        "election_commission": "The Electoral Commission",
        "website": "https://www.electoralcommission.org.uk",
        "voter_id": "Voter Authority Certificate or accepted photo ID",
        "registration": {
            "steps": [
                "Visit gov.uk/register-to-vote",
                "Provide your name, address, date of birth, and National Insurance number",
                "You'll receive a confirmation letter",
                "Check the electoral register to verify your registration",
                "Apply for a Voter Authority Certificate if you don't have photo ID"
            ],
            "documents_required": [
                "National Insurance number",
                "Photo ID for voting (passport, driving licence, or Voter Authority Certificate)"
            ],
            "online_portal": "https://www.gov.uk/register-to-vote",
            "deadline": "12 working days before an election",
            "processing_time": "Usually within 2 weeks"
        },
        "voting_process": [
            "Check your polling card for your polling station location",
            "Bring accepted photo ID to the polling station",
            "Give your name and address to the poll clerk",
            "Show your photo ID for verification",
            "Receive your ballot paper",
            "Go to a polling booth and mark an X next to your chosen candidate",
            "Fold the ballot and put it in the ballot box"
        ],
        "election_types": [
            {"type": "General Election", "frequency": "At least every 5 years", "description": "Elect 650 Members of Parliament (MPs) to the House of Commons"},
            {"type": "Local Elections", "frequency": "Usually annually", "description": "Elect local councillors"},
            {"type": "Devolved Elections", "frequency": "Every 4-5 years", "description": "Scottish Parliament, Welsh Senedd, Northern Ireland Assembly"},
            {"type": "By-Elections", "frequency": "As needed", "description": "Fill vacant parliamentary seats"}
        ],
        "eligibility": {
            "age": "Must be 18 or older on polling day (16 in Scotland and Wales for devolved elections)",
            "citizenship": "British, Irish, or qualifying Commonwealth citizen",
            "residency": "Must be registered at an address in the UK",
            "disqualifications": [
                "Members of the House of Lords (for General Elections)",
                "EU citizens (unless they have retained voting rights)",
                "People convicted of election offences"
            ]
        }
    }
}

# Frequently Asked Questions for RAG
FAQ_DATA = [
    {
        "question": "What is the Electoral College?",
        "answer": "The Electoral College is the system used in the United States to elect the President. It consists of 538 electors — each state gets a number of electors equal to its total Congressional representation (House seats + 2 Senators). To win the presidency, a candidate needs at least 270 electoral votes. Most states use a winner-take-all system, meaning the candidate who wins the popular vote in a state gets ALL of that state's electoral votes. Maine and Nebraska are exceptions, using a congressional district method.",
        "category": "electoral_system",
        "country": "usa"
    },
    {
        "question": "What is ranked-choice voting?",
        "answer": "Ranked-choice voting (RCV), also called instant-runoff voting, is a voting system where voters rank candidates in order of preference (1st choice, 2nd choice, etc.). If no candidate wins a majority of first-choice votes, the candidate with the fewest votes is eliminated, and their voters' second choices are redistributed. This process continues until one candidate has a majority. RCV is used in some U.S. cities and states (like Alaska and Maine), and in countries like Australia and Ireland.",
        "category": "electoral_system",
        "country": "general"
    },
    {
        "question": "What is EVM and VVPAT?",
        "answer": "EVM (Electronic Voting Machine) is the electronic device used in Indian elections to cast votes. It has a ballot unit with buttons next to candidate names and symbols. VVPAT (Voter Verifiable Paper Audit Trail) is an additional device attached to the EVM that prints a paper slip showing the candidate name and symbol you voted for. The slip is visible for 7 seconds through a window, then drops into a sealed box. This provides a physical paper trail to verify electronic votes.",
        "category": "voting_technology",
        "country": "india"
    },
    {
        "question": "Can I vote if I don't have a voter ID card?",
        "answer": "In India, while the EPIC (Voter ID card) is the primary identification, you can also use alternative photo IDs like Aadhaar card, passport, driving license, PAN card, or any government-issued photo ID. In the USA, ID requirements vary by state — some require photo ID, some accept non-photo ID, and some have no strict ID requirement. In the UK, you need a valid photo ID or a free Voter Authority Certificate. Always check your specific state/country requirements before Election Day.",
        "category": "voter_id",
        "country": "general"
    },
    {
        "question": "How do I check if I am registered to vote?",
        "answer": "In India: Visit electoralsearch.eci.gov.in or use the Voter Helpline App (1950). In the USA: Visit vote.gov or your state's Secretary of State website. In the UK: Contact your local Electoral Registration Office or check your polling card. It's important to verify your registration well before Election Day to allow time for corrections if needed.",
        "category": "registration",
        "country": "general"
    },
    {
        "question": "What is a constituency?",
        "answer": "A constituency is a defined geographical area that elects a representative. In India, there are 543 Lok Sabha constituencies and varying numbers of state assembly constituencies. In the USA, there are 435 Congressional districts for the House of Representatives. In the UK, there are 650 parliamentary constituencies. Each constituency typically elects one representative through a first-past-the-post system (the candidate with the most votes wins).",
        "category": "electoral_system",
        "country": "general"
    },
    {
        "question": "What is the Model Code of Conduct?",
        "answer": "The Model Code of Conduct (MCC) is a set of guidelines issued by the Election Commission of India that comes into effect as soon as elections are announced. It governs the conduct of political parties, candidates, and the government to ensure free and fair elections. Key rules include: no new government schemes or policies, no use of government resources for campaigning, no appeals to caste or communal feelings, and restrictions on political advertisements. Violation can lead to penalties and disqualification.",
        "category": "election_rules",
        "country": "india"
    },
    {
        "question": "What is gerrymandering?",
        "answer": "Gerrymandering is the practice of drawing electoral district boundaries in a way that gives one political party an unfair advantage. This is primarily a concern in the USA, where state legislatures often control redistricting. Common techniques include 'packing' (concentrating opposing voters in few districts) and 'cracking' (splitting opposing voters across many districts). Some states have adopted independent redistricting commissions to combat gerrymandering.",
        "category": "electoral_system",
        "country": "usa"
    },
    {
        "question": "What is NOTA?",
        "answer": "NOTA (None Of The Above) is an option on the Indian EVM that allows voters to officially reject all candidates. It was introduced by the Supreme Court of India in 2013. If you feel no candidate deserves your vote, you can press the NOTA button. However, NOTA votes don't affect the election result — the candidate with the most votes still wins even if NOTA gets more votes. It serves as a way for voters to express dissatisfaction with available choices.",
        "category": "voting_options",
        "country": "india"
    },
    {
        "question": "Can NRI vote in Indian elections?",
        "answer": "Yes, NRIs (Non-Resident Indians) can vote in Indian elections. They need to register as overseas voters using Form 6A on the NVSP portal. However, they must be physically present at their registered polling booth on Election Day to cast their vote — there is no postal or proxy voting facility for NRIs yet (though legislation for this is being considered). NRIs need a valid Indian passport for identification at the polling booth.",
        "category": "nri_voting",
        "country": "india"
    },
    {
        "question": "What happens if there is a tie in an election?",
        "answer": "In India, if two candidates receive the same number of votes, the result is decided by drawing of lots (a coin toss or similar random method) by the Returning Officer. In the USA, tied presidential elections go to the House of Representatives (each state gets one vote). For Congressional races, state laws vary — some require runoff elections. In the UK, tied results are decided by lot (drawing straws or similar), with the Returning Officer overseeing the process.",
        "category": "election_rules",
        "country": "general"
    },
    {
        "question": "What is a midterm election?",
        "answer": "Midterm elections in the USA occur halfway through a president's four-year term (every 4 years, 2 years after a presidential election). They include elections for all 435 seats in the House of Representatives, approximately one-third of the 100 Senate seats, and many state and local offices. Midterms are significant because they can shift the balance of power in Congress, potentially affecting the president's ability to pass legislation.",
        "category": "election_types",
        "country": "usa"
    }
]

# Simplified explanations for "Explain Like I'm 10" mode
SIMPLE_EXPLANATIONS = {
    "voting": "Voting is like choosing your favorite flavor of ice cream, but for leaders! Everyone gets to pick who they think would be the best person to make decisions for their city or country. You go to a special place, make your choice in secret, and the person most people choose becomes the leader.",
    "electoral_college": "Imagine each state is a team in a contest. Bigger states have more team members (votes). When people in a state vote, the team (state) gives ALL their votes to the winner. The first person to get 270 team votes (out of 538 total) wins and becomes President!",
    "registration": "Before you can vote, you need to sign up — kind of like joining a club. You tell the government your name and where you live, and they put you on a list of people who can vote. It's like getting a ticket that says 'you're allowed to play!'",
    "constituency": "A constituency is like dividing a big city into neighborhoods. Each neighborhood picks one person to speak for them. That way, everyone's area has someone looking out for their needs.",
    "evm": "An EVM is like a special calculator for votes. Instead of writing on paper, you press a button next to the picture of the person you want to vote for. The machine counts all the button presses to find out who won!"
}

def get_country_data(country: str) -> dict | None:
    """Get election data for a specific country."""
    key = country.lower().strip()
    # Handle common aliases
    aliases = {
        "us": "usa", "united states": "usa", "america": "usa", "united states of america": "usa",
        "britain": "uk", "united kingdom": "uk", "england": "uk", "great britain": "uk",
        "bharat": "india"
    }
    key = aliases.get(key, key)
    return ELECTION_DATA.get(key)

def get_all_countries() -> list[str]:
    """Get list of supported countries."""
    return list(ELECTION_DATA.keys())

def check_eligibility(country: str, age: int, is_citizen: bool, is_resident: bool) -> dict:
    """Check voting eligibility for a given country."""
    data = get_country_data(country)
    if not data:
        return {
            "eligible": False,
            "reason": f"Country '{country}' not found in our database. We currently support: India, USA, UK.",
            "next_steps": []
        }

    voting_age = data["voting_age"]
    issues = []
    next_steps = []

    if age < voting_age:
        issues.append(f"You must be at least {voting_age} years old to vote in {data['country']}. You are currently {age}.")
        years_left = voting_age - age
        next_steps.append(f"You'll be eligible to vote in {years_left} year(s). Start learning about the election process now!")

    if not is_citizen:
        issues.append(f"You must be a citizen of {data['country']} (or eligible category) to vote.")
        next_steps.append("Check if you qualify for citizenship or special voting rights.")

    if not is_resident:
        issues.append(f"You must be a resident of {data['country']} or registered in a constituency.")
        next_steps.append("If you've moved, update your voter registration with your new address.")

    if issues:
        return {
            "eligible": False,
            "reason": " | ".join(issues),
            "next_steps": next_steps
        }

    return {
        "eligible": True,
        "reason": f"You meet all the basic eligibility requirements to vote in {data['country']}!",
        "next_steps": [
            f"Register to vote at {data['registration']['online_portal']}",
            "Gather the required documents for registration",
            "Check upcoming election dates and deadlines"
        ]
    }
