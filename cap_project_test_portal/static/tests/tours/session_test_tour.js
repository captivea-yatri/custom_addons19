import tour from 'web_tour.tour';

const sessionSharingSteps = [...tour.stepUtils.goToAppSteps("cap_project_test.session_test_sub_menu", 'Go to the Session Test Menu.'),
 {
    trigger: '.o_web_client',
    content: 'Go to session portal view to select the "Session Test" Tests',
    run: function () {
        window.location.href = window.location.origin + '/my/sessions';
}, {
    id: 'session_sharing_feature',
    trigger: 'table > tbody > tr a:has(span:contains(Session Test))',
    content: 'Select "Session Test" project to go to project sharing feature for this project.',
}, {
    trigger: '.o_session_test',
    content: 'Wait the session test feature be loaded',
    run: function () {},
    }
];

