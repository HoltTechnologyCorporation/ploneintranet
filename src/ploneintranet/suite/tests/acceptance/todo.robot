*** Settings ***

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Resource  ../lib/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote
Library  DebugLibrary

Variables  variables.py

Test Setup  Prepare test browser
Test Teardown  Close all browsers


*** Test Cases ***

Alice can add a personal task
    Given I am logged in as the user alice_lindstrom
     Then I can go to the application  Todo
      And I have no personal tasks
     Then I create a personal task  My first task  Christian Stoney
     Then I delete the current document
      And I have no personal tasks

Allan can add a workspace task
    Given I am logged in as the user allan_neece
     Then I can go to the application  Todo
     Then I create a workspace task  My first task  Christian Stoney
     Then I delete the current document

*** Keywords ***

# See lib/keywords.robot in the section "case related keywords"

I have no personal tasks
    Wait until page contains element  jquery=#search-result .notice:contains(No results found)

I create a workspace task
    [arguments]  ${title}  ${assignee}
    Click link  New task
    I create a task  My first task  Christian Stoney

I create a personal task
    [arguments]  ${title}  ${assignee}
    Click Element  jquery=.create-document
    I create a task  My first task  Christian Stoney

I create a task
    [arguments]  ${title}  ${assignee}
    Wait for injection to be finished
    Input Text  xpath=//div[@class='panel-body']//input[@name='title']  text=${title}
    Input Text  xpath=//div[@class='panel-body']//textarea[@name='description']  text=Plan for success
    Input Text  css=label.assignee li.select2-search-field input  ${assignee}
    Wait Until Element Is visible  xpath=//span[@class='select2-match'][text()='${assignee}']
    Click Element  xpath=//span[@class='select2-match'][text()='${assignee}']
    Click Button  Create
    Wait Until Page Contains Element  jquery=.pat-notification-panel :contains('Close')
    Click Element  jquery=.pat-notification-panel :contains('Close')
    Click Element  css=#toggle-sidebar .open

I delete the current document
    Click Element  css=.quick-functions .icon-trash
    Wait for injection to be finished
    Click Button  I am sure, delete now
    Wait for injection to be finished
