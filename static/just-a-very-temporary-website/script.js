// declear conv as a global
var conv;

const loader = (filename) =>
{ // loads an html file
    return axios({
        method: 'get',
        url: filename
    })
    .then((response) =>
        {
            console.log("successfully got page");
            return Promise.resolve(response.data);
        })
    .catch((response) =>
        {
            return Promise.reject("could not load document");
        })
}

const send_msg = () =>
{
    let messagebox = document.getElementById('messagebox');
    let text = messagebox.value;
    if (text.length < 1)
    {
        return false;
    }
    messagebox.value = '';


    // inteTEXT does protect in most cases but that depends on browsers, this way we can be sure to filter bad strings
    text = text.replace('/</g', ';lt')
    text = text.replace('/>/g', ';gt')

    // add element that clears floats
    let clearf = document.createElement("div")
    clearf.style = "clear: both";
    document.getElementById('main').appendChild(clearf);

    // add message element
    let message = document.createElement("p");
    message.className = "main-message main-send";
    message.innerText = text;
    document.getElementById('main').appendChild(message);

    return true;
}

const logged_in = (response) =>
{ // gets executed on successful login


    localStorage.setItem("username", conv.username);

    loader('main.html')
    .then((response) =>
        {
            document.open();
            document.write(response);
            document.close();
        })
    .catch((response) =>
        {
            document.open();
            document.write("could not load main page :(")
            document.close();
        })

}

const login_failed = (response) =>
{ // gets executed on failed login
    document.getElementById('form-label').innerText = "login failed";
    document.getElementById('form-label').style = "color: red";
}

const login = () =>
{ // gets executed when the login button is pressed
    let username = document.getElementById('username-box').value;
    console.log('username: ',username , typeof(username));
    let password = document.getElementById('password-box').value;
    console.log('password: ',password , typeof(password));
    let chatroom = document.getElementById('chatroom-box').value;
    console.log('chatroom: ',chatroom , typeof(chatroom));

    const httpreg = /http..?\/\//;
    let url = window.location.href
    url = url.replace(httpreg, '');
    let newurl = '';
    for(var i=0; i < url.length; i++)
    {
        if (url.charAt(i) === '/')
        {
            break;
        }
        newurl += url.charAt(i);
    }
    if (url.startsWith('https'))
    {
        url = "https://"+newurl;
    }
    else
    {
        url = "http://"+newurl;
    }


    conv = new Chatroom({
        "username": username,
        "password": password,
        "chatroom": chatroom,
        "server": url
    })

    conv.login({
        callback_success: logged_in,
        callback_error: login_failed
    })
}


const main_loginpage = () =>
{
    // try get chatroom from url
    let url = window.location.href;
    let chatroom = url.split('?')[1].split("&")[0].split('=')[1]
    if (chatroom != undefined)
    {
        document.getElementById('chatroom-box').value = chatroom;
    }
}


const test_save = () =>
{
    localStorage.setItem("username", conv.username);
}
const test_load = () =>
{
    console.log(localStorage.getItem("username"));
}

// stop page from refreshing
if (!window.location.href.endsWith("?#"))
    window.location.href += '?#'

// load the login screen
loader('login.html')
.then((response) =>
    {
        document.open();
        document.write(response);
        document.close();
    })
.catch((response) =>
    {
        document.open();
        document.write("could not load login page :(")
        document.close();
    })

