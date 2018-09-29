from flask import Flask, render_template as template, request, url_for, send_from_directory
from datetime import datetime
from pytz import timezone
from multiprocessing import Lock
import os, socket

#import logging
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

app = Flask(__name__)

program = {
	'name': 'Affluenza',
	'investor_deposit': 54637.31,
	'basis_balance': 59501.78,
	'current_balance': 54974.86,
	'current_equity': 54974.86,
	'high_water_mark': 58458.85,
	'open_trades': 0,
	'accounts': {
		'ben141':{
			'name': "Benjamin Lyman",
			'deposit': 3000.00,
			'basis': 3195.39
		},
		'brett592': {
			'name': "Brett Lyman",
			'deposit': 25000.00,
			'basis': 26628.24
		},
		'daniel653': {
			'name': "Daniel Lyman",
			'deposit': 1753.52,
			'basis': 1867.73
		},
		'devin589': {
			'name': "Devin Christensen",
			'deposit': 3000.00,
			'basis': 3195.39
		},
		'eddie34': {
			'name': "Eddie Lyman",
			'deposit': 4000.00,
			'basis': 4260.52
		},
		'jacob238': {
			'name': "Jacob Nielson",
			'deposit': 1000.00,
			'basis': 1065.13
		},
		'joe416': {
			'name': "Joseph Lyman",
			'deposit': 500.00,
			'basis': 532.56
		},
		'marie462': {
			'name': "Marie Bernhardt",
			'deposit': 5000.00,
			'basis': 5325.65
		},
		'mat643': {
			'name': "Mat Lyman",
			'deposit': 11383.79,
			'basis': 12125.21
		},
		'lymanfx42':{
			'name': "LymanFX, LLC",
			'deposit': 1273.85,
			'basis': 1305.96
		}
	}
}


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')


@app.route('/tbody/<account>')
def get_tbody(account):
	global program
	program_open_trades = program['open_trades']
	response = ""
	rows = []
	if account in program['accounts']:
		
		lymanfx_basis = program['accounts']['lymanfx42']['basis']
		lymanfx_percent = lymanfx_basis/program['basis_balance']
		lymanfx_deposit = program['accounts']['lymanfx42']['deposit']
		lymanfx_balance = lymanfx_percent * program['current_equity'] # against full balance, since no commission is charged to lymanfx
		
		collected_commission = program['accounts']['lymanfx42']['deposit'] # sum of all commission "deposits" (each time we rebase)
		uncollected_commission = 0
		total_investor_balance = investor_balance = program['current_equity']-lymanfx_balance
		if investor_balance > program['high_water_mark']:
			uncollected_commission = (investor_balance - program['high_water_mark'])/3
			investor_balance = investor_balance - uncollected_commission
		investor_profit = investor_balance-program['investor_deposit']
		investor_return = round((investor_profit/program['investor_deposit'])*100,1)
		
		if account == "lymanfx42":
			account_deposit = lymanfx_deposit
			account_balance = lymanfx_balance
		else:
			account_deposit = program['accounts'][account]['deposit']
			account_percent = account_deposit/program['investor_deposit']
			account_balance = account_percent * investor_balance
		account_profit = account_balance - account_deposit
		account_percent_return = round(((account_balance-account_deposit)/account_deposit)*100,1)
		
		rows.append([program["accounts"][account]["name"],None])
		rows.append(["Deposit","${:,.2f}".format(account_deposit)])
		rows.append(["Balance","${:,.2f}".format(account_balance)])
		rows.append(["Profit/Loss",('-' if account_profit < 0 else '+')+"${:,.2f}".format(abs(account_profit))])
		rows.append(["Return",('-' if account_profit < 0 else '+')+"{:,.1f}%".format(abs(account_percent_return))])
		
		if account == "lymanfx42":
			overall_profit = program['current_equity']-program['investor_deposit']
			overall_return = round((overall_profit / program['investor_deposit'])*100,1)
			rows.append(["Affluenza",None])
			rows.append(["Deposit","${:,.2f}".format(program['investor_deposit'])])
			rows.append(["Closed Balance","${:,.2f}".format(program['current_balance'])])
			rows.append(["Open Balance","${:,.2f}".format(program['current_equity'])])
			rows.append(["Profit/Loss",('-' if overall_profit < 0 else '+')+"${:,.2f}".format(abs(overall_profit))])
			rows.append(["Return",('-' if overall_return < 0 else '+')+"{:,.1f}%".format(abs(overall_return))])
			rows.append(["Investors",None])
			rows.append(["Balance","${:,.2f}".format(total_investor_balance)])
			rows.append(["High Water Mark","${:,.2f}".format(program['high_water_mark'])])
			rows.append(["Uncollected Commission","${:,.2f}".format(uncollected_commission)])
			rows.append(["Adjusted Balance","${:,.2f}".format(investor_balance)])
			rows.append(["Profit",('-' if investor_profit < 0 else '+')+"${:,.2f}".format(abs(investor_profit))])
			rows.append(["Return",('-' if investor_profit < 0 else '+')+"{:,.1f}%".format(abs(investor_return))])
			rows.append([" ",None])
	
	rows.append(["Open Positions",str(program_open_trades)])
	for row in rows:
		response += template('row_template.html',name=row[0],value=row[1])
	
	response += '<tr><td align="right" colspan="2" style="font-size: 12px; color: #AAA">'+datetime.now(timezone('US/Mountain')).strftime('%D %I:%M:%S %p %Z')+'</td></tr>'
	return response


@app.route('/balance/<account>')
def balance(account):
	global program
	response = "Invalid account."
	
	if account == "lymanfx42" or account in program['accounts']:
		print("["+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"] Account balance check: "+account)
		timeout = 5000 if program['open_trades'] > 0 else 30000
		response = ('<html><head>'
						'<title>LymanFX Affluenza</title>'
						'<script src="//cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"> </script>'
						'<script type="text/javascript">function update_tbody() { $.get("/tbody/'+account+'", function (response) { $("#main_tbody").html(response); }); window.setTimeout(update_tbody, '+str(timeout)+'); }</script>'
						'</head><body style="font-family: Arial;">'
							'<table>'
								'<tbody id="main_tbody">'+get_tbody(account)+'</tbody>'
							'</table>'
						'</body>'
						'<script type="text/javascript">window.setTimeout(update_tbody, '+str(timeout)+')</script>'
					'</html>')
	
	return response


@app.route('/update')
def update():
	global program
	password = request.args.get('p','')
	if password == "IbJFJjdTxrvYlrpCYA6f":
		program['current_balance'] = float(request.args.get('b',''))
		program['current_equity'] = float(request.args.get('e',''))
		program['open_trades'] = int(request.args.get('n',''))
		return 'successful'
	else:
		return 'incorrect password: '+password


#if __name__ == "__main__":
#	print('Starting web server...')
#	app.run(debug=False,host='192.168.1.80',port=80)

