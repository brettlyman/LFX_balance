from flask import Flask, render_template as template, request, url_for, send_from_directory
from datetime import datetime
from pytz import timezone
from multiprocessing import Lock
import os, socket, joblib

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

cirsumvent_commissions = 0.00 # 419.70+570.23
cirsumvent_3_commissions = 0.00

investors = {
	'lymanfx42': { # even though LymanFX technically isn't an "investor"...
		'name': 'LymanFX, LLC',
		'deposit': 7281.59+2318.46+cirsumvent_commissions+cirsumvent_3_commissions
	},
	'ben141': {
		'name': 'Ben Lyman',
		'deposit': 3500+2000
	},
	'brett592': {
		'name': 'Brett Lyman',
		'deposit': 70000
	},
	'daniel653': {
		'name': 'Daniel Lyman',
		'deposit': 2000
	},
	'devin589': {
		'name': 'Devin Christensen',
		'deposit': 4000+20000+26000
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
		'deposit': 23992.41
	},
	'notben': {
		'name': 'Ben Bradley',
		'deposit': 1000+3000
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
	'laurelc': {
		'name': 'Laurel Christensen',
		'deposit': 37500.00+15000.00+30000
	},
	'toddg': {
		'name': 'Todd Grant',
		'deposit': 15000.00
	}
}

accounts = [
	{
		'account_id': 496675395,
		'name': 'Cirsumvent',
		'original_deposit': 193876.74,
		'deposit': 193876.74+cirsumvent_commissions,
		'balance': 196966.26,
		'equity': 199834.49,
		'reset_balance': 193876.74,
		'period_target': 200708.07,
		'target': 207448.11,
		'lymanfx': 7281.59+cirsumvent_commissions,
		'high_water_mark': 188605.62,
		'open_positions': 958,
		'last_update': datetime.now(timezone('US/Mountain')),
		'investors': {
			'ben141': 6011.81,
			'brett592': 70000.00,
			'daniel653': 1732.58,
			'devin589': 24171.04,
			'eddie34': 1944.18,
			'jacob238': 988.06,
			'joe416': 494.03,
			'mat643': 24749.43,
			'notben': 4004.02,
			'laurelc': 37500.00,
			'toddg': 15000.00
		}
	},
	{
		'account_id': 497826702,
		'name': 'Cirsumvent III',
		'original_deposit': 77955.39,
		'deposit': 77955.39+cirsumvent_3_commissions,
		'balance': 77955.39,
		'equity': 77955.39,
		'reset_balance': 77955.39,
		'period_target': 77955.39,
		'target': 77955.39,
		'lymanfx': 2318.46,
		'high_water_mark': 75636.93,
		'open_positions': 0,
		'last_update': datetime.now(timezone('US/Mountain')),
		'investors': {
			'laurelc': 19636.93+30000,
			'devin589': 26000
		}
	}
]


for i in range(0,len(accounts)):
	if os.path.isfile(str(accounts[i]['account_id'])+'.pkl'):
		account = joblib.load(str(accounts[i]['account_id'])+'.pkl')
		accounts[i]['balance'] = account['balance']
		accounts[i]['equity'] = account['equity']
		accounts[i]['target'] = account['target']
		accounts[i]['period_target'] = account['period_target']
		accounts[i]['reset_balance'] = account['reset_balance']
		accounts[i]['open_positions'] = account['open_positions']
		accounts[i]['last_update'] = account['last_update']


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
		rows.append([investor['name'],None,None,None])
		rows.append(["Deposit","${:,.2f}".format(investor['deposit']),None,None])
		investor_total_balance = 0
		for account in accounts:
			lymanfx_deposit, lymanfx_balance = get_lymanfx_balance(account)
			if username == 'lymanfx42' or username in account['investors']:
				account_name = account['name']
				
				rows.append([account_name,None,None,None])
				rows.append([None,None,None,"Updated: "+account['last_update'].strftime('%D %I:%M:%S %p %Z')])
				
				investors_deposit = account['deposit']-lymanfx_deposit
				orig_investors_balance = investors_balance = account['balance']-lymanfx_balance
				uncollected_commission = 0
				if 'high_water_mark' in account and investors_balance > account['high_water_mark']:
					uncollected_commission = (investors_balance-account['high_water_mark'])/3
					investors_balance -= uncollected_commission
				investors_profit = investors_balance-investors_deposit
				investors_return = round((investors_profit/investors_deposit)*100,2)
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
					investor_percent_return = round(((investor_profit)/investor_deposit)*100,2)
					rows.append(["Deposit/Carryover","${:,.2f}".format(investor_deposit),None,None])
					rows.append(["Balance","${:,.2f}".format(investor_balance),None,None])
					rows.append(["Profit/Loss",('-' if investor_profit < 0 else '+')+"${:,.2f}".format(abs(investor_profit)),None,None])
					rows.append(["Return",('-' if investor_profit < 0 else '+')+"{:,.2f}%".format(abs(investor_percent_return)),None,None])
				if username == "lymanfx42":
					account_profit = account['balance']-account['original_deposit']
					account_return = round((account_profit/account['original_deposit'])*100,2)
					if investor_deposit > 0:
						rows.append(["---","---","gray",None])
					rows.append(["Total Deposit","${:,.2f}".format(account['deposit']),None,None])
					rows.append(["Reset Balance","${:,.2f}".format(account['reset_balance']),"#AAA",None])
					rows.append(["Closed Balance","${:,.2f}".format(account['balance']),None,None])
					rows.append(["Open Balance","${:,.2f}".format(account['equity']),"green" if account['equity'] > account['balance'] else None,None])
					rows.append(["Period Target","${:,.2f}".format(account['period_target']),"#AAA",None])
					rows.append(["Reset Target","${:,.2f}".format(account['target']),"#AAA",None])
					rows.append(["---","---","gray",None])
					rows.append(["Profit/Loss",('-' if account_profit < 0 else '+')+"${:,.2f}".format(abs(account_profit)),None,None])
					rows.append(["Overall Return",('-' if account_return < 0 else '+')+"{:,.2f}%".format(abs(account_return)),None,None])
					if 'lymanfx' in account:
						rows.append(["Investor Balance","${:,.2f}".format(orig_investors_balance),None,None])
						rows.append(["High Water Mark","${:,.2f}".format(account['high_water_mark']),None,None])
						rows.append(["Uncollected Commission","${:,.2f}".format(uncollected_commission),"green",None])
						rows.append(["Adj Investor Balance","${:,.2f}".format(investors_balance),None,None])
						rows.append(["Investor Profit",('-' if investors_profit < 0 else '+')+"${:,.2f}".format(abs(investors_profit)),None,None])
						rows.append(["Investor Return",('-' if investors_profit < 0 else '+')+"{:,.2f}%".format(abs(investors_return)),None,None])
						rows.append(["---","---","gray",None])
					rows.append(["Open Units",str(int(account['open_positions'])),None,None])
					rows.append(["---","---","gray",None])
					account_investors = []
					for inv in account['investors']:
						if inv != "lymanfx42":
							inv_deposit = account['investors'][inv]
							inv_percent = inv_deposit/investors_deposit
							inv_balance = inv_percent*investors_balance
							account_investors.append({ 'name': investors[inv]['name'], 'balance': inv_balance })
					for acct_inv in sorted(account_investors, key=lambda i: i['name']):
						rows.append([acct_inv['name'],"${:,.2f}".format(acct_inv['balance']),"#AAA",None])
		investor_total_profit = investor_total_balance-investor['deposit']
		investor_total_percent_return = round(((investor_total_profit)/investor['deposit'])*100,2)
		rows.insert(2,["Balance","${:,.2f}".format(investor_total_balance),None,None])
		rows.insert(3,["Profit/Loss",('-' if investor_total_profit < 0 else '+')+"${:,.2f}".format(abs(investor_total_profit)),None,None])
		rows.insert(4,["Return",('-' if investor_total_profit < 0 else '+')+"{:,.2f}%".format(abs(investor_total_percent_return)),None,None])
	for row in rows:
		response += template('row_template.html',name=row[0],value=row[1],color=row[2],date_string=row[3])
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
	logo = '<img src="/static/logo.png" />' if username not in ['karl','ryan','abhishek','telnicky','evelyn'] else ''
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
						'window.setTimeout(update_tbody, 30000); '
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
				'window.setTimeout(update_tbody, 30000)'
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
				accounts[i]['period_target'] = float(request.args.get('pt',''))
				accounts[i]['reset_balance'] = float(request.args.get('rb',''))
				accounts[i]['open_positions'] = float(request.args.get('n',''))
				accounts[i]['last_update'] = datetime.now(timezone('US/Mountain'))
				joblib.dump(accounts[i], str(accounts[i]['account_id'])+'.pkl')
				return 'successful'
	else:
		return 'fail.'


#if __name__ == "__main__":
#	print('Starting web server...')
#	app.run(debug=False,host='0.0.0.0',port=80)
