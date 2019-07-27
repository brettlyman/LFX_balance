from flask import Flask, render_template as template, request, url_for, send_from_directory
from datetime import datetime
from pytz import timezone
from multiprocessing import Lock
import os, socket

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

investors = {
	'lymanfx42': { # even though LymanFX technically isn't an "investor"...
		'name': 'LymanFX, LLC',
		'deposit': 2034.39+58.94+4.50+356.52+106.49+362.63+213.14+6.19+34.73+201.18+85.19
	},
	'ben141': {
		'name': 'Ben Lyman',
		'deposit': 3500+2000
	},
	'brett592': {
		'name': 'Brett Lyman',
		'deposit': 29000+62582.76
	},
	'daniel653': {
		'name': 'Daniel Lyman',
		'deposit': 2000
	},
	'devin589': {
		'name': 'Devin Christensen',
		'deposit': 4000
	},
	'eddie34': {
		'name': 'Eddie Lyman',
		'deposit': 2000
	},
	'jacob238': {
		'name': 'Jacob Nielson',
		'deposit': 1000
	},
	'joe416': {
		'name': 'Joseph Lyman',
		'deposit': 500
	},
	'marie462': {
		'name': 'Marie Bernhardt',
		'deposit': 0
	},
	'mat643': {
		'name': 'Mathew Lyman',
		'deposit': 16883.79
	},
	'notben': {
		'name': 'Ben Bradley',
		'deposit': 1000
	},
	'karl': {
		'name': 'Karl Lilley',
		'deposit': 2500+856.74
	},
	'ryan': {
		'name': 'Ryan Nguyen',
		'deposit': 2500+856.74
	},
	'abhishek': {
		'name': 'Abhishek Andhavarapu',
		'deposit': 2500
	},
	'telnicky': {
		'name': 'Travis Elnicky',
		'deposit': 1000.00
	},
	'evelyn': {
		'name': 'Evelyn Sharp',
		'deposit': 1065.36
	}
}

accounts = [
	{
		'account_id': 21962,
		'name': 'Banana Stand - Stable',
		'original_deposit': 36481.31,
		'deposit': 36481.31+58.94+356.52+362.63+6.19+201.18,
		'balance': 39556.12,
		'equity':39821.29,
		'target': 40068.30,
		'lymanfx': 1078.70+58.94+356.52+362.63+6.19+201.18,
		'high_water_mark': 37376.85,
		'open_positions': 0.15,
		'investors': {
			'ben141': 2597.05,
			'brett592': 12641.04,
			'daniel653': 1493.85,
			'devin589': 2555.74,
			'eddie34': 1676.29,
			'jacob238': 851.91,
			'joe416': 425.96,
			'mat643': 12295.09,
			'notben': 865.68
		}
	},
	{
		'account_id': 21185,
		'name': 'Banana Stand - Risky',
		'original_deposit': 15346.18,
		'deposit': 15346.18+4.50+106.49+213.14+34.73+85.19,
		'balance': 16761.44,
		'equity': 16878.46,
		'target': 17166.59,
		'lymanfx': 735.72+4.50+106.49+213.14+34.73+85.19,
		'high_water_mark': 15509.11,
		'open_positions': 0.07,
		'investors': {
			'brett592': 10652.79,
			'mat643': 2387.05,
			'devin589': 1000.00,
			'ben141': 570.62
		}
	},
	{
		'account_id': 22803,
		'name': 'Bixin',
		'original_deposit': 75000.00,
		'deposit': 75000.00,
		'balance': 74976.00,
		'equity': 74976.00,
		'target': 77787.60,
		'open_positions': 0,
		'investors': {
			'karl': 2500.00,
			'ryan': 2500.00,
			'abhishek': 1643.26,
			'brett592': 64226.02,
			'ben141': 2000.00,
			'evelyn': 1065.36,
			'telnicky': 1065.36
		}
	}
]


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')


@app.route('/tbody/<username>')
def get_tbody(username):
	global accounts, investors
	response = ""
	rows = []
	if username in investors:
		investor = investors[username]
		rows.append([investor['name'],None])
		rows.append(["Deposit","${:,.2f}".format(investor['deposit'])])
		investor_total_balance = 0
		num_accounts = 0
		total_open_positions = 0
		for account in accounts:
			lymanfx_deposit, lymanfx_balance = get_lymanfx_balance(account)
			if username == 'lymanfx42' or username in account['investors']:
				num_accounts += 1
				total_open_positions += account['open_positions']
				account_name = account['name']
				
				rows.append([account_name,None])
				investors_deposit = account['deposit']-lymanfx_deposit
				orig_investors_balance = investors_balance = account['balance']-lymanfx_balance
				uncollected_commission = 0
				if 'high_water_mark' in account and investors_balance > account['high_water_mark']:
					uncollected_commission = (investors_balance-account['high_water_mark'])/3
					investors_balance -= uncollected_commission
				investors_profit = investors_balance-investors_deposit
				investors_return = round((investors_profit/investors_deposit)*100,1)
				if username == "lymanfx42":
					investor_deposit = lymanfx_deposit
					investor_balance = lymanfx_balance
				else:
					investor_deposit = account['investors'][username]
					investor_percent = investor_deposit/investors_deposit
					investor_balance = investor_percent*investors_balance
				investor_total_balance += investor_balance
				if investor_deposit > 0:
					investor_profit = investor_balance-investor_deposit
					investor_percent_return = round(((investor_profit)/investor_deposit)*100,1)
					#rows.append(["Deposit","${:,.2f}".format(investor_deposit)]) # hidden since this is "basis" deposit, not actual...
					rows.append(["Balance","${:,.2f}".format(investor_balance)])
					#rows.append(["Profit/Loss",('-' if investor_profit < 0 else '+')+"${:,.2f}".format(abs(investor_profit))])
					#rows.append(["Return",('-' if investor_profit < 0 else '+')+"{:,.1f}%".format(abs(investor_percent_return))])
				if username == "lymanfx42":
					account_profit = account['balance']-account['original_deposit']
					account_return = round((account_profit/account['original_deposit'])*100,1)
					if investor_deposit > 0:
						rows.append(["---","---"])
					rows.append(["Total Deposit","${:,.2f}".format(account['deposit'])])
					rows.append(["Closed Balance","${:,.2f}".format(account['balance'])])
					rows.append(["Open Balance","${:,.2f}".format(account['equity'])])
					rows.append(["Target Balance","${:,.2f}".format(account['target'])])
					rows.append(["---","---"])
					rows.append(["Profit/Loss",('-' if account_profit < 0 else '+')+"${:,.2f}".format(abs(account_profit))])
					rows.append(["Overall Return",('-' if account_return < 0 else '+')+"{:,.1f}%".format(abs(account_return))])
					if 'lymanfx' in account:
						rows.append(["Investor Balance","${:,.2f}".format(orig_investors_balance)])
						rows.append(["High Water Mark","${:,.2f}".format(account['high_water_mark'])])
						rows.append(["Uncollected Commission","${:,.2f}".format(uncollected_commission)])
						rows.append(["Adj Investor Balance","${:,.2f}".format(investors_balance)])
						rows.append(["Investor Profit",('-' if investors_profit < 0 else '+')+"${:,.2f}".format(abs(investors_profit))])
						rows.append(["Investor Return",('-' if investors_profit < 0 else '+')+"{:,.1f}%".format(abs(investors_return))])
						rows.append(["---","---"])
				rows.append(["Open Units",str(account['open_positions'])])
		investor_total_profit = investor_total_balance-investor['deposit']
		investor_total_percent_return = round(((investor_total_profit)/investor['deposit'])*100,1)
		rows.insert(2,["Balance","${:,.2f}".format(investor_total_balance)])
		rows.insert(3,["Profit/Loss",('-' if investor_total_profit < 0 else '+')+"${:,.2f}".format(abs(investor_total_profit))])
		rows.insert(4,["Return",('-' if investor_total_profit < 0 else '+')+"{:,.1f}%".format(abs(investor_total_percent_return))])
	for row in rows:
		response += template('row_template.html',name=row[0],value=row[1])
	response += '<tr><td align="right" colspan="2" style="font-size: 12px; color: #AAA">'
	response += datetime.now(timezone('US/Mountain')).strftime('%D %I:%M:%S %p %Z')
	response += '</td></tr>'
	return response


def get_lymanfx_balance(account):
	if 'lymanfx' in account:
		lymanfx_percent = account['lymanfx']/account['deposit']
		return account['lymanfx'], lymanfx_percent * account['balance']
	return 0, 0


@app.route('/balance/<username>')
def balance(username):
	global accounts, investors
	tbody_url = '/tbody/{0}?{1}'.format(username,"all" if request.args.get("all") != None else "")
	logo = '<img src="/static/logo.png" />' if username not in ['karl','ryan','abhishek'] else ''
	return (''
		'<html>'
			'<head>'
				'<title>LymanFX</title>'
				'<script src="//cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js">'
				'</script>'
				'<script type="text/javascript">'
					'function update_tbody() { '
						'$.get("'+tbody_url+'", function (response) { '
							'$("#main_tbody").html(response);'
						'}); '
						'window.setTimeout(update_tbody, 10000); '
					'}'
				'</script>'
			'</head>'
			'<body style="font-family: Arial;">'
				'<table style="width: 300px">'
					'<thead>'
						'<tr>'
							'<td colspan="2" style="text-align: center">'+logo+'</td>'
						'</tr>'
					'</thead>'
					'<tbody id="main_tbody">'+get_tbody(username)+'</tbody>'
				'</table>'
			'</body>'
			'<script type="text/javascript">'
				'window.setTimeout(update_tbody, 10000)'
			'</script>'
		'</html>')


@app.route('/update')
def update():
	global accounts
	password = request.args.get('p','')
	account_id = int(request.args.get('a',''))
	if password == "IbJFJjdTxrvYlrpCYA6f":
		for i in range(0,len(accounts)):
			if accounts[i]['account_id'] == account_id:
				accounts[i]['balance'] = float(request.args.get('b',''))
				accounts[i]['equity'] = float(request.args.get('e',''))
				accounts[i]['target'] = float(request.args.get('t',''))
				accounts[i]['open_positions'] = float(request.args.get('n',''))
				return 'successful'
	else:
		return 'fail.'


#if __name__ == "__main__":
#	print('Starting web server...')
#	app.run(debug=False,host='0.0.0.0',port=80)
