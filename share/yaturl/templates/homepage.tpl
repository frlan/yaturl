<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>
    <title>yatURL.net - Yet another tiny URL service</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    <meta name="generator" content="Geany 0.19" />
    <link rel="stylesheet" href="/default.css" type="text/css"/>
</head>

<body>
	<div id="container">
		<div id="header"><span>yaturl.net</span></div>
		<div id="main">
			<p>Please insert your URL here:</p>
			%(msg)s
				<form action="/URLRequest" method="post">
					<p><input name="URL" type="text" size="50"/>
					<input type="submit" value="Submit"/></p>
				</form>
		</div>
		<div id="footer"><span><a href="/ContactUs">Contact Us</a> &nbsp;&nbsp; <a href="/About">About</a></span></div>	</div>
</body>
</html>
