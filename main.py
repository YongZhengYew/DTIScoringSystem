import sys
import json
from PyQt6 import QtCore
from PyQt6.QtWidgets import QStackedWidget, QApplication, QPushButton, QLineEdit, QWidget, QFormLayout, QMessageBox, QListWidget, QLabel, QHBoxLayout, QPlainTextEdit, QRadioButton, QButtonGroup
from PyQt6.QtCore import Qt
import firebase_admin
from firebase_admin import credentials, db
import random

cred = credentials.Certificate(".auth/dtidatabase-firebase-adminsdk-4skrm-3de593b09b.json")
default_app = firebase_admin.initialize_app(cred, {
	"databaseURL":"https://dtidatabase-default-rtdb.europe-west1.firebasedatabase.app/"
	})
ref = db.reference("/")

class QuestionCode():
    staticSubjectParamDirectory = {
        "A": "Subject1",
        "B": "Subject2"
    }

    staticDifficultyParamDirectory = {
        "A": "Easy",
        "B": "Medium",
        "C": "Hard"
    }

    staticCount = 2

    def __init__(self, codeString):
        self.codeString = codeString
        self.params = {
            "Subject": QuestionCode.staticSubjectParamDirectory[codeString[0]],
            "Difficulty": QuestionCode.staticDifficultyParamDirectory[codeString[1]],
        }
        self.paramKeyList = list(self.params)

    def getCodeString(self):
        return self.codeString

    def getParamsAsString(self):
        res = ""
        for key, val in self.params.items():
            res += key + ": " + val + "\n"
        return res

    def refreshCodeString(self, index, newThing):
        newCodeString = list(self.codeString)
        newCodeString[index] = newThing
        self.codeString = "".join(newCodeString)

    def changeSubject(self, newSubject):
        self.params["Subject"] = QuestionCode.staticSubjectParamDirectory[newSubject]
        self.refreshCodeString(0, newSubject)

    def changeDifficulty(self, newDifficulty):
        self.params["Difficulty"] = QuestionCode.staticDifficultyParamDirectory[newDifficulty]
        self.refreshCodeString(1, newDifficulty)

    def getParams(self):
        return self.params

class MainProgram(QWidget):
    def __init__(self):
        super().__init__()
        self.FILE_EXTENSION_PLAYERACCOUNT = ".playerAccount"
        self.FILE_EXTENSION_FACILACCOUNT = ".facilAccount"
        self.setWindowTitle("Hello there")
        self.resize(1600, 1200)

        self.pageStack = QStackedWidget(self)
        self.readyPlayerDict = {}
        self.readyPlayerNameList = []
        self.currPlayerIndex = 0
        self.currPlayerName = ""
        self.currPlayerDict = {}
        self.localQuestionList = {}
        self.definedCorrectAnswerStore = 0
        self.newQuestionCodeStore = QuestionCode("AA")
        self.currQuestionDict = {}
        self.currCorrectAnswerIndex = ""
        self.tempPlayerPointsDict = {}

        self.lockPage = QWidget()
        self.facilStartPage = QWidget()
        self.facilAuthPage = QWidget()
        self.questionBankPage = QWidget()
        self.playerAdmissionsPage = QWidget()
        self.accountCreationPage = QWidget()
        self.loginPage = QWidget()
        self.enterQuestionCodePage = QWidget()
        self.questionPlayPage = QWidget()
        self.collapsePage = QWidget()

        self.lockPageUI()
        self.facilStartPageUI()
        self.facilAuthPageUI()
        self.questionBankPageUI()
        self.playerAdmissionsPageUI()
        self.accountCreationPageUI()
        self.loginPageUI()
        self.enterQuestionCodePageUI()
        self.questionPlayPageUI()
        self.collapsePageUI()

        self.refreshQuestionList()

        self.pageStack.addWidget(self.lockPage)
        self.pageStack.addWidget(self.facilStartPage)
        self.pageStack.addWidget(self.facilAuthPage)
        self.pageStack.addWidget(self.questionBankPage)
        self.pageStack.addWidget(self.playerAdmissionsPage)
        self.pageStack.addWidget(self.accountCreationPage)
        self.pageStack.addWidget(self.loginPage)
        self.pageStack.addWidget(self.enterQuestionCodePage)
        self.pageStack.addWidget(self.questionPlayPage)
        self.pageStack.addWidget(self.collapsePage)
        self.show()

    def calcPoints(self):
        return 10
    
    def readPlayerAccount(self, accName):
        req = ref.child("Players").child(accName)
        got = req.get()
        if got is not None:
            return got
        else:
            return False
    
    def setPlayerAccount(self, accName, changeDict):
        got = ref.child("Players").child(accName).get()
        if got is not None:
            gotDict = json.loads(got)
            gotDict.update(changeDict)
            ref.child("Players").update({accName: json.dumps(gotDict)})
            return True
        else:
            self.errBox("No such player!")
            return False

    def countDigits(self, num):
        count = 0
        curr = num
        while curr != 0:
            curr //= 10
            count += 1
        return count

    def errBox(self, msg, title="Error"):
        msgBox = QMessageBox()
        msgBox.setText(msg)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.StandardButtons.Ok)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.StandardButtons.Ok:
            return
    def successBox(self, msg, title="Success!"):
        msgBox = QMessageBox()
        msgBox.setText(msg)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.StandardButtons.Ok)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.StandardButtons.Ok:
            return
    def noticeBox(self, msg, title="Notice!"):
        msgBox = QMessageBox()
        msgBox.setText(msg)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.StandardButtons.Ok)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.StandardButtons.Ok:
            return
    
    def isInvalidInput(self, arr):
        res = False
        for item in arr:
            res = res or (str.isspace(item) or item == "")
        return res

    def createAccount(self):
        accName = self.accountCreationPage.nameInput.text()
        accPhoneNumber = self.accountCreationPage.phoneNumberInput.text()
        accPassword = self.accountCreationPage.passwordInput.text()
        accConfirmPassword = self.accountCreationPage.passwordConfirmInput.text()

        if self.isInvalidInput([accName, accPhoneNumber, accPassword, accConfirmPassword]):
            return self.errBox("One or more fields have been left blank.")

        try:
            accPhoneNumber = int(self.accountCreationPage.phoneNumberInput.text())
        except ValueError:
            return self.errBox("There seems to be a mistake in the phone number.")
        
        if self.countDigits(accPhoneNumber) != 8:
            return self.errBox("Wrong number of digits in phone number. There should be 8.")
        
        if self.accountCreationPage.passwordInput.text() != self.accountCreationPage.passwordConfirmInput.text():
            return self.errBox("New password and confirm new password are different")
        else:
            accPassword = self.accountCreationPage.passwordInput.text()

        #if os.path.exists(accFileName) and os.path.isfile(accFileName):
        if ref.child("Players").child(accName).get() is not None:
            return self.errBox("That account already exists. Try logging in instead!")
        else:
            accDict = {
                "AccountName": accName,
                "PhoneNumber": accPhoneNumber,
                "Password": accPassword,
                "Points": 0,
            }
            ref.child("Players").child(accName).set(json.dumps(accDict))
            return self.successBox("Account Created.")

    def goTo_FacilStartPage(self):
        self.pageStack.setCurrentWidget(self.facilStartPage)
    def goTo_FacilAuthPage(self):
        self.pageStack.setCurrentWidget(self.facilAuthPage)
    def goTo_AccountCreationPage(self):
        self.pageStack.setCurrentWidget(self.accountCreationPage)
    def goTo_PlayerAdmissionsPage(self):
        self.pageStack.setCurrentWidget(self.playerAdmissionsPage)
    def goTo_LoginPage(self):
        self.pageStack.setCurrentWidget(self.loginPage)
    def goTo_QuestionBankPage(self):
        self.refreshQuestionList()
        self.pageStack.setCurrentWidget(self.questionBankPage)
    def goTo_EnterQuestionCodePage(self):
        self.pageStack.setCurrentWidget(self.enterQuestionCodePage)
    def goTo_QuestionPlayPage(self):
        self.prepQuestionPlayPage()
        self.pageStack.setCurrentWidget(self.questionPlayPage)
    def goTo_CollapsePage(self):
        self.setWinnings()
        self.pageStack.setCurrentWidget(self.collapsePage)
    
    def abortGameInProgress(self):
        self.noticeBox("Game aborted! No scores have changed.")
        self.pageStack.setCurrentWidget(self.playerAdmissionsPage)

    def attemptLogin(self):
        accName = self.loginPage.nameInput.text()
        accPassword = self.loginPage.passwordInput.text()
        if self.isInvalidInput([accName, accPassword]):
            return self.errBox("One or more fields have been left blank.")

        got = ref.child("Players").child(accName).get()
        gotDict = json.loads(got) if got is not None else None
        if gotDict is not None:
            if accPassword != gotDict["Password"]:
                return self.errBox("Password is incorrect.")
            self.addReadyPlayer(accName)
            self.readyPlayerDict[accName] = gotDict
            print(self.readyPlayerNameList)
            return self.successBox("Player {accName} ready.".format(accName=accName))
        else:
            return self.errBox("No such account! Try creating an account first.")

    def addReadyPlayer(self, accName):
        if accName in self.readyPlayerNameList or self.playerAdmissionsPage.readyList.findItems(accName, Qt.MatchFlags.MatchExactly):
            return self.errBox("Player already in ready list!")
        else:
            self.readyPlayerNameList.append(accName)
            self.playerAdmissionsPage.readyList.addItem(accName)

    def removePlayerFromPlayerAdmissionsPageList(self):
        playersToBeRemoved = self.playerAdmissionsPage.readyList.selectedItems()
        for player in playersToBeRemoved:
            accName = player.text()
            if accName in self.readyPlayerNameList or self.playerAdmissionsPage.readyList.findItems(accName, Qt.MatchFlags.MatchExactly):
                self.readyPlayerNameList.remove(accName)
                self.playerAdmissionsPage.readyList.takeItem(self.playerAdmissionsPage.readyList.row(player))
            else:
                return self.errBox("THIS ERROR SHOULD NOT OCCUR. Player {accName} is not in ready list.").format(accName=accName)


    def attemptLockFacilLogin(self):
        accName = self.lockPage.facilNameInput.text()
        accPassword = self.lockPage.facilPasswordInput.text()
        if self.isInvalidInput([accName, accPassword]):
            return self.errBox("One or more fields have been left blank.")

        got = ref.child("Facil").child(accName).get()
        gotDict = json.loads(got) if got is not None else None
        if gotDict is not None:
            if accPassword != gotDict["Password"]:
                return self.errBox("Password is incorrect.")
            self.goTo_FacilStartPage()
        else:
            return self.errBox("No such account.")

    def attemptFacilLogin(self):
        accName = self.facilAuthPage.facilNameInput.text()
        accPassword = self.facilAuthPage.facilPasswordInput.text()
        if self.isInvalidInput([accName, accPassword]):
            return self.errBox("One or more fields have been left blank.")

        got = ref.child("Facil").child(accName).get()
        gotDict = json.loads(got) if got is not None else None
        if gotDict is not None:
            if accPassword != gotDict["Password"]:
                return self.errBox("Password is incorrect.")
            self.goTo_FacilStartPage()
        else:
            return self.errBox("No such account.")

    def testConnect(self):
        print("hi!")

    def refreshQuestionList(self):
        self.questionBankPage.questionList.clear()
        attemptCurrQuestions = ref.child("Questions").order_by_key().get()
        if attemptCurrQuestions is None:
            self.localQuestionList = "EMPTY"
        else:
            currQuestions = dict(attemptCurrQuestions)
            self.localQuestionList = currQuestions
            print(self.localQuestionList)
            print(self.localQuestionList)
            for key in self.localQuestionList:
                self.questionBankPage.questionList.addItem(key)
    
    def displayQuestionOnQuestionBankPage(self):
        self.questionBankPage.questionTextDisplay.clear()
        self.questionBankPage.questionAnswersList.clear()
        self.questionBankPage.definedCorrectAnswerDisplay.clear()
        self.questionBankPage.questionCodeParserDisplay.clear()

        if self.localQuestionList == "EMPTY":
            return self.noticeBox("No questions!")
        else:
            currItem = self.questionBankPage.questionList.currentItem()
            if currItem is not None:
                currQuestionKey = self.questionBankPage.questionList.currentItem().text()
                currSelQuestion = json.loads(self.localQuestionList[currQuestionKey])
                currContent = currSelQuestion["Content"]
                currAnswerList = currSelQuestion["AnswerList"]
                currCAI = currSelQuestion["CorrectAnswerIndex"]
                currCorrectAnswer = currAnswerList[currCAI]
                nQCode = QuestionCode(currSelQuestion["QuestionCode"])
                currQuestionCodeParsed = nQCode.getParamsAsString()

                self.questionBankPage.questionTextDisplay.setText(currContent)
                for answer in currAnswerList:
                    self.questionBankPage.questionAnswersList.addItem(answer)
                self.questionBankPage.definedCorrectAnswerDisplay.setText(currCorrectAnswer)
                self.questionBankPage.questionCodeParserDisplay.setText(currQuestionCodeParsed)
            else:
                pass

    def defineCorrectAnswer(self):
        definedCorrectAnswerIndex = self.questionBankPage.newQuestionAnswerList.indexFromItem(self.questionBankPage.newQuestionAnswerList.currentItem()).row()
        print(definedCorrectAnswerIndex)
        self.definedCorrectAnswerStore = definedCorrectAnswerIndex
        self.questionBankPage.definedNewCorrectAnswerDisplay.setText(self.questionBankPage.newQuestionAnswerList.currentItem().text())

    def subjectRadioToggle(self):
        if self.questionBankPage.subject1Radio.isChecked():
            self.newQuestionCodeStore.changeSubject("A")
        if self.questionBankPage.subject2Radio.isChecked():
            self.newQuestionCodeStore.changeSubject("B")
        print(self.newQuestionCodeStore.getCodeString())
        
    def difficultyRadioToggle(self):
        if self.questionBankPage.easyRadio.isChecked():
            self.newQuestionCodeStore.changeDifficulty("A")
        if self.questionBankPage.mediumRadio.isChecked():
            self.newQuestionCodeStore.changeDifficulty("B")
        if self.questionBankPage.hardRadio.isChecked():
            self.newQuestionCodeStore.changeDifficulty("C")
        print(self.newQuestionCodeStore.getCodeString())

    def submitNewAnswer(self):
        self.questionBankPage.newQuestionAnswerList.addItem(self.questionBankPage.newQuestionAnswerInput.text())
        self.questionBankPage.newQuestionAnswerInput.clear()

    def submitNewQuestion(self):
        title = self.questionBankPage.newQuestionTitle.text()
        if title in dict(ref.child("Questions").order_by_key().get()):
            return self.errBox("That question already exists!")
        else:
            content = self.questionBankPage.newQuestionContent.toPlainText()
            answerList = []
            for index in range(self.questionBankPage.newQuestionAnswerList.count()):
                answerList.append(self.questionBankPage.newQuestionAnswerList.item(index).text())
            newAnswerDict = {
                "Title": title,
                "Content": content,
                "AnswerList": answerList,
                "CorrectAnswerIndex": self.definedCorrectAnswerStore,
                "QuestionCode": self.newQuestionCodeStore.getCodeString()
            }
            ref.child("Questions").child(title).set(json.dumps(newAnswerDict))

            self.questionBankPage.newQuestionTitle.clear()
            self.questionBankPage.newQuestionContent.clear()
            self.questionBankPage.newQuestionAnswerList.clear()
            self.questionBankPage.definedNewCorrectAnswerDisplay.clear()

            return self.successBox("New Question Submitted")

    def cyclePlayerTurn(self):
        print("_________")
        print(self.readyPlayerNameList)
        print(self.currPlayerName)
        print(self.currPlayerIndex)
        if self.currPlayerIndex < len(self.readyPlayerNameList) - 1:
            self.currPlayerIndex += 1
        else:
            self.currPlayerIndex = 0
        
        self.currPlayerName = self.readyPlayerNameList[self.currPlayerIndex]
        self.currPlayerDict = self.readyPlayerDict[self.currPlayerName]
        self.enterQuestionCodePage.currPlayerTurnDisplay.setText(self.currPlayerName)
        print(self.currPlayerName)
        print("_________")


    def startNewGame(self):
        for name in self.readyPlayerNameList:
            self.tempPlayerPointsDict[name] = 0

        self.currPlayerName = random.choice(self.readyPlayerNameList)
        self.currPlayerDict = self.readyPlayerDict[self.currPlayerName]
        self.currPlayerIndex = self.readyPlayerNameList.index(self.currPlayerName)

        self.enterQuestionCodePage.currPlayerTurnDisplay.setText(self.currPlayerName)
        self.goTo_EnterQuestionCodePage()

    def submitQuestionCode(self):
        matchList = []
        searchCodeString = self.enterQuestionCodePage.enterQuestionInput.text()
        for questionKey, questionDictString in self.localQuestionList.items():
            questionDict = json.loads(questionDictString)
            if searchCodeString == questionDict["QuestionCode"]:
                matchList.append(questionKey)
        matchLength = len(matchList)
        if matchLength > 0:
            randptr = random.randint(0, len(matchList) - 1)
            self.currQuestionDict = json.loads(self.localQuestionList[matchList[randptr]])
            self.currCorrectAnswerIndex = self.currQuestionDict["CorrectAnswerIndex"]
            self.goTo_QuestionPlayPage()
        else:
            return self.errBox("No matching questions!")
    
    def prepQuestionPlayPage(self):
        self.questionPlayPage.titleDisplay.clear()
        self.questionPlayPage.contentDisplay.clear()
        self.questionPlayPage.choiceList.clear()
        self.questionPlayPage.playerScores.clear()

        activeQuestionDict = self.currQuestionDict
        activeTitle = activeQuestionDict["Title"]
        activeContent = activeQuestionDict["Content"]

        self.questionPlayPage.titleDisplay.setText(activeTitle)
        self.questionPlayPage.contentDisplay.setText(activeContent)

        choices = activeQuestionDict["AnswerList"]
        for choice in choices:
            self.questionPlayPage.choiceList.addItem(choice)
        
        self.questionPlayPage.playerScores.setText(self.allPlayerTempPoints())
    
    def submitPlayQuestion(self):
        currChoice = self.questionPlayPage.choiceList.selectedItems()[0].text()
        correctAns = self.currQuestionDict["AnswerList"][self.currQuestionDict["CorrectAnswerIndex"]]
        print(currChoice)
        print(correctAns)
        if correctAns == currChoice:
            pointsToAdd = self.calcPoints()
            self.tempPlayerPointsDict[self.currPlayerName] += pointsToAdd
            self.successBox("Correct! Player {currPlayer} gets {pointsToAdd} points for a total of {newPoints}.".format(currPlayer=self.currPlayerName, pointsToAdd=pointsToAdd, newPoints=self.tempPlayerPointsDict[self.currPlayerName]))
        else:
            self.noticeBox("Wrong answer!")
        
        self.cyclePlayerTurn()
        self.goTo_EnterQuestionCodePage()

    def setWinnings(self):
        sortedScoreList = sorted(self.tempPlayerPointsDict, key=self.tempPlayerPointsDict.get)
        winnerName = sortedScoreList[-1]
        winnerEarnings = self.tempPlayerPointsDict[winnerName]
        newWinnerTotalPoints = self.readyPlayerDict[winnerName]["Points"] + winnerEarnings

        winnerDict = self.readyPlayerDict[winnerName]

        winnerDict.update({"Points": newWinnerTotalPoints})
        self.readyPlayerDict.update({winnerName: winnerDict})
        self.setPlayerAccount(winnerName, winnerDict)

        self.collapsePage.scoreBoard.setText(self.allPlayerTotalPoints())
        self.collapsePage.winnerDisplay.setText(winnerName)
        return self.successBox("{winner} has won for a new total of {newPoints} points!".format(winner=winnerName, newPoints=newWinnerTotalPoints))
        
    def allPlayerTempPoints(self):
        res = ""
        for accName, points in self.tempPlayerPointsDict.items():
            res += accName + ": " + str(points) + "\n"
        return res

    def allPlayerTotalPoints(self):
        res = ""
        for accName, accDict in self.readyPlayerDict.items():
            res += accName + ": " + str(accDict["Points"]) + "\n"
        return res


    def lockPageUI(self):
        layout = QFormLayout()

        self.lockPage.facilNameInput = QLineEdit()
        layout.addRow("Name",self.lockPage.facilNameInput)

        self.lockPage.facilPasswordInput = QLineEdit()
        layout.addRow("Password",self.lockPage.facilPasswordInput)

        self.lockPage.loginButton = QPushButton("&Login")
        self.lockPage.loginButton.clicked.connect(self.attemptLockFacilLogin)
        layout.addRow(self.lockPage.loginButton)

        self.lockPage.setLayout(layout)

    def facilStartPageUI(self):
        layout = QFormLayout()

        self.facilStartPage.loginPlayersButton = QPushButton("Log In Players")
        self.facilStartPage.loginPlayersButton.clicked.connect(self.goTo_PlayerAdmissionsPage)
        layout.addRow(self.facilStartPage.loginPlayersButton)

        self.facilStartPage.questionBankButton = QPushButton("Question Bank")
        self.facilStartPage.questionBankButton.clicked.connect(self.goTo_QuestionBankPage)
        layout.addRow(self.facilStartPage.questionBankButton)

        self.facilStartPage.setLayout(layout)

    def facilAuthPageUI(self):
        layout = QFormLayout()

        self.facilAuthPage.facilNameInput = QLineEdit()
        layout.addRow("Name",self.facilAuthPage.facilNameInput)

        self.facilAuthPage.facilPasswordInput = QLineEdit()
        layout.addRow("Password",self.facilAuthPage.facilPasswordInput)

        self.facilAuthPage.loginButton = QPushButton("&Login")
        self.facilAuthPage.loginButton.clicked.connect(self.attemptFacilLogin)

        self.facilAuthPage.abortLoginButton = QPushButton("&Back")
        self.facilAuthPage.abortLoginButton.clicked.connect(self.goTo_PlayerAdmissionsPage)

        layout.addRow(self.facilAuthPage.abortLoginButton, self.facilAuthPage.loginButton)

        self.facilAuthPage.setLayout(layout)
    
    def questionBankPageUI(self):
        layout = QFormLayout()

        subLayout = QHBoxLayout()
        self.questionBankPage.questionList = QListWidget()
        self.questionBankPage.questionList.currentRowChanged.connect(self.displayQuestionOnQuestionBankPage)
        self.questionBankPage.questionTextDisplay = QLabel()
        self.questionBankPage.questionTextDisplay.setFixedSize(500,100)
        self.questionBankPage.questionAnswersList = QListWidget()
        self.questionBankPage.definedCorrectAnswerDisplay = QLabel()
        self.questionBankPage.definedCorrectAnswerDisplay.setFixedSize(50,10)
        self.questionBankPage.questionCodeParserDisplay = QLabel()
        self.questionBankPage.questionCodeParserDisplay.setFixedSize(100,50)
        subLayout.addWidget(self.questionBankPage.questionList)
        subLayout.addWidget(self.questionBankPage.questionTextDisplay)
        subLayout.addWidget(self.questionBankPage.questionAnswersList)
        subLayout.addWidget(self.questionBankPage.definedCorrectAnswerDisplay)
        subLayout.addWidget(self.questionBankPage.questionCodeParserDisplay)
        layout.addRow(subLayout)

        self.questionBankPage.newQuestionTitle = QLineEdit()
        self.questionBankPage.newQuestionContent = QPlainTextEdit()
        layout.addRow(self.questionBankPage.newQuestionTitle, self.questionBankPage.newQuestionContent)

        self.questionBankPage.newQuestionAnswerInput = QLineEdit()
        self.questionBankPage.newQuestionAnswerList = QListWidget()
        layout.addRow(self.questionBankPage.newQuestionAnswerInput, self.questionBankPage.newQuestionAnswerList)

        subjectLayout = QFormLayout()
        subjectButtonGroup = QButtonGroup(self.questionBankPage)
        self.questionBankPage.subject1Radio = QRadioButton()
        self.questionBankPage.subject2Radio = QRadioButton()
        self.questionBankPage.subject1Radio.toggled.connect(self.subjectRadioToggle)
        self.questionBankPage.subject2Radio.toggled.connect(self.subjectRadioToggle)
        subjectButtonGroup.addButton(self.questionBankPage.subject1Radio)
        subjectButtonGroup.addButton(self.questionBankPage.subject2Radio)
        subjectLayout.addRow("Subject 1", self.questionBankPage.subject1Radio)
        subjectLayout.addRow("Subject 2", self.questionBankPage.subject2Radio)

        difficultyLayout = QFormLayout()
        difficultyButtonGroup = QButtonGroup(self.questionBankPage)
        self.questionBankPage.easyRadio = QRadioButton()
        self.questionBankPage.mediumRadio = QRadioButton()
        self.questionBankPage.hardRadio = QRadioButton()
        self.questionBankPage.easyRadio.toggled.connect(self.difficultyRadioToggle)
        self.questionBankPage.mediumRadio.toggled.connect(self.difficultyRadioToggle)
        self.questionBankPage.hardRadio.toggled.connect(self.difficultyRadioToggle)
        difficultyButtonGroup.addButton(self.questionBankPage.easyRadio)
        difficultyButtonGroup.addButton(self.questionBankPage.mediumRadio)
        difficultyButtonGroup.addButton(self.questionBankPage.hardRadio)
        difficultyLayout.addRow("Easy", self.questionBankPage.easyRadio)
        difficultyLayout.addRow("Medium", self.questionBankPage.mediumRadio)
        difficultyLayout.addRow("Hard", self.questionBankPage.hardRadio)

        combLayout = QHBoxLayout()
        combLayout.addLayout(subjectLayout)
        combLayout.addLayout(difficultyLayout)
        layout.addRow(combLayout)

        self.questionBankPage.definedNewCorrectAnswerDisplay = QLabel()
        layout.addRow(self.questionBankPage.definedNewCorrectAnswerDisplay)

        self.questionBankPage.defineCorrectAnswerButton = QPushButton("&Define Correct Answer")
        self.questionBankPage.defineCorrectAnswerButton.clicked.connect(self.defineCorrectAnswer)
        self.questionBankPage.submitNewAnswerButton = QPushButton("Submit &Answer")
        self.questionBankPage.submitNewAnswerButton.clicked.connect(self.submitNewAnswer)
        layout.addRow(self.questionBankPage.defineCorrectAnswerButton, self.questionBankPage.submitNewAnswerButton)

        self.questionBankPage.submitNewQuestionButton = QPushButton("Submit New &Question")
        self.questionBankPage.submitNewQuestionButton.clicked.connect(self.submitNewQuestion)
        layout.addRow(self.questionBankPage.submitNewQuestionButton)

        self.questionBankPage.backButton = QPushButton("&Back")
        self.questionBankPage.backButton.clicked.connect(self.goTo_FacilStartPage)
        self.questionBankPage.refreshButton = QPushButton("&Refresh")
        self.questionBankPage.refreshButton.clicked.connect(self.goTo_QuestionBankPage)
        layout.addRow(self.questionBankPage.backButton, self.questionBankPage.refreshButton)

        self.questionBankPage.setLayout(layout)

    def playerAdmissionsPageUI(self):
        layout = QFormLayout()

        self.playerAdmissionsPage.createAnAccountButton = QPushButton("&Create New Account!")
        self.playerAdmissionsPage.createAnAccountButton.clicked.connect(self.goTo_AccountCreationPage)
        layout.addRow(self.playerAdmissionsPage.createAnAccountButton)

        self.playerAdmissionsPage.proceedToLoginButton = QPushButton("&Login")
        self.playerAdmissionsPage.proceedToLoginButton.clicked.connect(self.goTo_LoginPage)
        layout.addRow(self.playerAdmissionsPage.proceedToLoginButton)

        self.playerAdmissionsPage.readyList = QListWidget()
        layout.addRow(self.playerAdmissionsPage.readyList)

        self.playerAdmissionsPage.removePlayerButton = QPushButton("&Remove Selected Players")
        self.playerAdmissionsPage.removePlayerButton.clicked.connect(self.removePlayerFromPlayerAdmissionsPageList)
        layout.addRow(self.playerAdmissionsPage.removePlayerButton)

        self.playerAdmissionsPage.startGameButton = QPushButton("&Start Game!")
        self.playerAdmissionsPage.startGameButton.clicked.connect(self.startNewGame)
        layout.addRow(self.playerAdmissionsPage.startGameButton)

        self.playerAdmissionsPage.proceedToFacilAuthPageButton = QPushButton("&Faciliator Page")
        self.playerAdmissionsPage.proceedToFacilAuthPageButton.clicked.connect(self.goTo_FacilAuthPage)
        layout.addRow(self.playerAdmissionsPage.proceedToFacilAuthPageButton)

        self.playerAdmissionsPage.setLayout(layout)

    def accountCreationPageUI(self):
        layout = QFormLayout()

        self.accountCreationPage.nameInput = QLineEdit()
        layout.addRow("Name",self.accountCreationPage.nameInput)

        self.accountCreationPage.phoneNumberInput = QLineEdit()
        layout.addRow("Phone Number",self.accountCreationPage.phoneNumberInput)

        self.accountCreationPage.passwordInput = QLineEdit()
        layout.addRow("New Password",self.accountCreationPage.passwordInput)

        self.accountCreationPage.passwordConfirmInput = QLineEdit()
        layout.addRow("Confirm New Password",self.accountCreationPage.passwordConfirmInput)

        self.accountCreationPage.createAccountButton = QPushButton("&Create Account")
        self.accountCreationPage.createAccountButton.clicked.connect(self.createAccount)

        self.accountCreationPage.finishCreatingAccountsButton = QPushButton("&Done")
        self.accountCreationPage.finishCreatingAccountsButton.clicked.connect(self.goTo_PlayerAdmissionsPage)

        layout.addRow(self.accountCreationPage.finishCreatingAccountsButton, self.accountCreationPage.createAccountButton)
        self.accountCreationPage.setLayout(layout)
    
    def loginPageUI(self):
        layout = QFormLayout()

        self.loginPage.nameInput = QLineEdit()
        layout.addRow("Name",self.loginPage.nameInput)

        self.loginPage.passwordInput = QLineEdit()
        layout.addRow("Password",self.loginPage.passwordInput)

        self.loginPage.loginButton = QPushButton("&Login")
        self.loginPage.loginButton.clicked.connect(self.attemptLogin)

        self.loginPage.abortLoginButton = QPushButton("&Back")
        self.loginPage.abortLoginButton.clicked.connect(self.goTo_PlayerAdmissionsPage)

        layout.addRow(self.loginPage.abortLoginButton, self.loginPage.loginButton)
        self.loginPage.setLayout(layout)
    
    def enterQuestionCodePageUI(self):
        layout = QFormLayout()

        self.enterQuestionCodePage.currPlayerTurnDisplay = QLabel()
        layout.addRow(self.enterQuestionCodePage.currPlayerTurnDisplay)

        self.enterQuestionCodePage.enterQuestionInput = QLineEdit()
        self.enterQuestionCodePage.submitQuestionCodeButton = QPushButton("&Submit Code!")
        self.enterQuestionCodePage.submitQuestionCodeButton.clicked.connect(self.submitQuestionCode)
        layout.addRow(self.enterQuestionCodePage.enterQuestionInput, self.enterQuestionCodePage.submitQuestionCodeButton)

        self.enterQuestionCodePage.setLayout(layout)

    def questionPlayPageUI(self):
        layout = QFormLayout()

        self.questionPlayPage.titleDisplay = QLabel()
        layout.addRow(self.questionPlayPage.titleDisplay)

        self.questionPlayPage.contentDisplay = QLabel()
        layout.addRow(self.questionPlayPage.contentDisplay)

        self.questionPlayPage.choiceList = QListWidget()
        self.questionPlayPage.playerScores = QLabel()
        layout.addRow(self.questionPlayPage.choiceList, self.questionPlayPage.playerScores)

        self.questionPlayPage.chooseButton = QPushButton("&Submit")
        self.questionPlayPage.chooseButton.clicked.connect(self.submitPlayQuestion)
        layout.addRow(self.questionPlayPage.chooseButton)

        self.questionPlayPage.collapseButton = QPushButton("Collapse!")
        self.questionPlayPage.collapseButton.clicked.connect(self.goTo_CollapsePage)
        self.questionPlayPage.abortButton = QPushButton("Abort")
        self.questionPlayPage.abortButton.clicked.connect(self.abortGameInProgress)
        layout.addRow(self.questionPlayPage.collapseButton, self.questionPlayPage.abortButton)

        self.questionPlayPage.setLayout(layout)

    def collapsePageUI(self):
        layout = QFormLayout()

        self.collapsePage.scoreBoard = QLabel()
        layout.addRow(self.collapsePage.scoreBoard)

        self.collapsePage.winnerDisplay = QLabel()
        layout.addRow(self.collapsePage.winnerDisplay)

        self.collapsePage.backButton = QPushButton("Back")
        self.collapsePage.backButton.clicked.connect(self.goTo_PlayerAdmissionsPage)
        layout.addRow(self.collapsePage.backButton)

        self.collapsePage.setLayout(layout)

app = QApplication(sys.argv)
mainProgram = MainProgram()

sys.exit(app.exec())