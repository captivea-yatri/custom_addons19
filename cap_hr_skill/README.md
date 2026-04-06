Cap Hr Skill aims to simplify processes for enhanced easy to use.
---------------------------------------------------------

From the Cap Hr skill, One can easily initiate the skill validation request process with just a clicks using the employee App.
Then, click on the skill validation request menu to proceed.

Hr Skill request make your Resume strong.

All skill requests were completed successfully, and subsequently, all skills were showcased in the employee form views under 
their corresponding skill types, accompanied by the date of accomplishment

Access Right
---------------------------------------------------------
HR skill requests are contingent upon approval by the designated approver.
Users possess visible access to employee details within the res user models, wherein access to employee information is configured.
Skills are added to the employee form views only upon approval by the approver.


Configuration
--------------------------------------------------------

We will configure the settings in three areas, namely Skill, Skills Domain, and Skills Validator. Once configured, users will be
able to make requests, albeit with high authority permissions.
All configurations are defined below

Skill
--------------------------------------------------------

First go to skill type menu and then define skill type and then create skill type.
Then proceed to create skills with attributes such as name, points, validation type, skill domain, and survey.
There are three types of validation: Knowledge Board, Certification, and Recording.

Type of validation
---------------------------------------------------------

Type of Validation basically three type like Knowledge Board, Certification, and Recording it has already been discussed.

Knowledge Board
------------------------------------------------------------
Knowledge Board skill type when request skill validation skill type will Knowledge Board skill then validator will schedule
meeting in this meeting validator ask some random question with requester if it will be done validator will do the request in
success state if failed then validator move the request into failed state.

Certification
------------------------------------------------------------

In certification job, when the requester requests skill validation, he directly appears in the scheduled state, after receiving 
a mail containing a link to the aptitude test.
When we click on the link then test start tab will appear, when we start the test, our validator is with us, if the test score is 
75 or 75 +, we will directly request the success state, if the test score is less than 75, then it will automatically failed state.

Recording
------------------------------------------------------------
When you request recording Type Of Valivation, you will first perform on your topic and make screen record it.
When you make a request, you will have to add the link of our recording video or anything in the URL fields.
Must remember in recording type skill Url fields is required.

Skills Domain
------------------------------------------------------------

In the skill domain, there are two fields: one for the name and the other for the skill type.
We set skill type name into name fields and select the type of into Skill Type fields.

Skills Validator
----------------------------------------------------------


In the skill validator, there are three fields: skill domain, validator, and company. When selecting 
a skill domain and validator, multiple companies can be chosen simultaneously. However, if no company 
is specified for a skill domain, then admin is automatically assigned. When a skill request is made,
the validator associated with the skill domain will be responsible for approval.

Create Professional skill Request
------------------------------------------------------

When you want to request skill validation request by completing the required fields and then saving the request. 
The request will be forwarded to the designated approver specified in the skill validator settings.
Upon approval, the approver schedules the skill validation request, transitioning it into a scheduled state.
Subsequently, the user arranges a meeting for the requester. If the requester meets the qualification criteria, the 
request transitions to a success state; otherwise, it enters a failed state.

For skill types categorized as certification, upon saving the request, it automatically enters a scheduled state. 
Subsequently, an email notification is sent, initiating the assessment process. If the user achieves a score of 75% or
higher, the request transitions to a success state; otherwise, it remains in a failed state.

Track your request
--------------------------------------------------------

Upon creating a skill request, it enters the requested state. Subsequently, the validator schedules the request, following
which it transitions to either a success or failed state based on the assessment outcome. Upon reaching either state, the 
corresponding activity is called and closed accordingly.