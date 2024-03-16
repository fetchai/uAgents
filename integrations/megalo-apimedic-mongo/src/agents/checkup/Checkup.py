import json
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field


checkup_protocol = Protocol("Medical Checkup")
TOKEN = 'YOUR_APIMEDIC_TOKEN'


class UserInput(Model):
    symptom : str = Field("Symptom related to the sickess that you have: ")
    age: int = Field("What is Your current Age?:  ")
    gender : str = Field("Male / Female?:  ")



def get_SymptomID(symptomName: str):
    URI = f'https://sandbox-healthservice.priaid.ch/symptoms?token={TOKEN}&format=json&language=en-gb'
    symptomStore = json.loads(requests.get(URI).text)
    for symptom in symptomStore:
        if(symptom["Name"] == symptomName):
            return symptom["ID"]
    return None


#Get diagnosis report of [issues and specialisation] via medicAPI/diagnosis endpoint
def get_diagnosis(symptomID: int, age: int, gender: str):
    yearBirth = 2023 - age
    URI = f"https://sandbox-healthservice.priaid.ch/diagnosis?symptoms=[{symptomID}]&gender={gender}&year_of_birth={yearBirth}&token={TOKEN}&format=json&language=en-gb"
    diagnoseStore = json.loads(requests.get(URI).text)
    issues = []
    specialisation = []
    for diagnosis in diagnoseStore:
        issues.append(diagnosis["Issue"]["Name"])
        ICDsplit = diagnosis["Issue"]["IcdName"].split(';')
        for issue in ICDsplit:
            issues.append(issue)
        for job in diagnosis["Specialisation"]:
            specialisation.append(job["Name"])
    diagnosisData = {
        "issues": list(set(issues)),
        "specialisations": list(set(specialisation))
    }
    return diagnosisData


#Frame the prompt for fetched diagnosis report in a String [diagnosis report]
def frameDiagnosis(symptom: str, diagnosisDict: dict):
    prompt = f"If you're having {symptom}, you might be having other similar affects such: "
    for issue in diagnosisDict["issues"]:
        prompt += f"\n- {issue}"
    prompt += f"\n\n In which case it is recommended to see one of these specialists: "
    for job in diagnosisDict["specialisations"]:
        prompt += f"\n- {job}"
    return prompt


#Checkup and pass for clinics suggestions with Clinics Agent
@checkup_protocol.on_message(model=UserInput, replies = UAgentResponse)
async def on_requestCheckup(ctx: Context, sender: str, msg: UserInput):
    try:
        symptomID = get_SymptomID(msg.symptom)
        ctx.logger.info(f"Symptom ID: {data}")
        #Incorrrect Symptom -> Faulty Case
        if(symptomID == None):
            await ctx.send(
                sender, 
                UAgentResponse(message = "Your symptoms do not match anything we know of!", type = UAgentResponseType.FINAL)
            )
        else:
            #Forward for further Diagnosis
            diagnosisData = get_diagnosis(symptomID, int(msg.age), str(msg.gender))
            diagnosisReport = frameDiagnosis(msg.symptom, diagnosisData)
            await ctx.send(
                sender, 
                UAgentResponse(message = diagnosisReport, type = UAgentResponseType.FINAL)
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))



agent.include(checkup_protocol)
