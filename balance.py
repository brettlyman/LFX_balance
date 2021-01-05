from flask import Flask, render_template as template, request, url_for, send_from_directory
from datetime import datetime
from pytz import timezone
from multiprocessing import Lock
import os, socket, joblib

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
#logging.basicConfig(filename='error.log',level=logging.DEBUG)

app = Flask(__name__)

investors = {
	'lymanfx42': {
		'name': 'LymanFX, LLC',
		'deposit': 0.000000001
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
		'deposit': 4000+20000+26000+30000
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
	'laurelc': {
		'name': 'Laurel Christensen',
		'deposit': 37500+15000+30000+15000
	},
	'toddg': {
		'name': 'Todd Grant',
		'deposit': 15000+15000
	}
}

accounts = [
	{
		'account_id': 496675395,
		'name': 'd\'Artagnan',
		'original_deposit': 338036.47,
		'deposit': 338036.47,
		'balance': 338036.47,
		'equity': 338036.47,
		'lymanfx': 0,
		'high_water_mark': 338036.47,
		'last_update': datetime.now(timezone('US/Mountain')),
		'investors': {
			'ben141': 6507.55,
			'brett592': 75772.32,
			'daniel653': 1875.45,
			'devin589': 82307.72,
			'eddie34': 2104.50,
			'jacob238': 1069.54,
			'joe416': 534.77,
			'mat643': 26790.31,
			'notben': 4334.20,
			'laurelc': 105503.18,
			'toddg': 31236.93
		}
	}
]


for i in range(0,len(accounts)):
	if os.path.isfile(str(accounts[i]['account_id'])+'.pkl'):
		account = joblib.load(str(accounts[i]['account_id'])+'.pkl')
		accounts[i]['balance'] = account['balance']
		accounts[i]['equity'] = account['equity']
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
		investor_total_equity = 0
		for account in accounts:
			lymanfx_deposit, lymanfx_balance, lymanfx_equity = get_lymanfx_balance(account)
			if username == 'lymanfx42' or username in account['investors']:
				account_name = account['name']
				
				rows.append([account_name,None,None,None])
				rows.append([None,None,None,"Updated: "+account['last_update'].strftime('%D %I:%M:%S %p %Z')])
				
				investors_deposit = account['deposit']-lymanfx_deposit
				orig_investors_balance = investors_balance = account['balance']-lymanfx_balance
				investors_equity = account['equity']-lymanfx_equity
				uncollected_commission = 0
				if 'high_water_mark' in account and investors_balance > account['high_water_mark']:
					uncollected_commission = (investors_balance-account['high_water_mark'])/3
					investors_balance -= uncollected_commission
				if 'high_water_mark' in account and investors_equity > account['high_water_mark']:
					uncollected_equity_commission = (investors_equity-account['high_water_mark'])/3
					investors_equity -= uncollected_equity_commission
				investors_profit = investors_balance-investors_deposit
				investors_return = round((investors_profit/investors_deposit)*100,2)
				if username == "lymanfx42":
					investor_deposit = lymanfx_deposit
					investor_balance = lymanfx_balance
					investor_equity = lymanfx_equity
				else:
					investor_deposit = account['investors'][username]
					investor_percent = investor_deposit/investors_deposit
					investor_balance = investor_percent*investors_balance
					investor_equity = investor_percent*investors_equity
				investor_total_balance += investor_balance 
				investor_total_equity += investor_equity
				if investor_deposit > 0:
					investor_profit = investor_balance-investor_deposit
					investor_percent_return = round(((investor_profit)/investor_deposit)*100,2)
					rows.append(["Deposit/Carryover","${:,.2f}".format(investor_deposit),None,None])
					rows.append(["Balance","${:,.2f}".format(investor_balance),None,None])
					rows.append(["Live Balance","${:,.2f}".format(investor_equity),"#AAA",None])
					rows.append(["Profit/Loss",('-' if investor_profit < 0 else '+')+"${:,.2f}".format(abs(investor_profit)),None,None])
					rows.append(["Return",('-' if investor_profit < 0 else '+')+"{:,.2f}%".format(abs(investor_percent_return)),None,None])
				if username == "lymanfx42":
					account_profit = account['balance']-account['original_deposit']
					account_return = round((account_profit/account['original_deposit'])*100,2)
					if investor_deposit > 0:
						rows.append(["---","---","gray",None])
					rows.append(["Total Deposit","${:,.2f}".format(account['deposit']),None,None])
					rows.append(["Closed Balance","${:,.2f}".format(account['balance']),None,None])
					rows.append(["Open Balance","${:,.2f}".format(account['equity']),"green" if account['equity'] > account['balance'] else None,None])
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
		rows.insert(3,["Live Balance","${:,.2f}".format(investor_total_equity),"#AAA",None])
		rows.insert(4,["Profit/Loss",('-' if investor_total_profit < 0 else '+')+"${:,.2f}".format(abs(investor_total_profit)),None,None])
		rows.insert(5,["Return",('-' if investor_total_profit < 0 else '+')+"{:,.2f}%".format(abs(investor_total_percent_return)),None,None])
	for row in rows:
		response += template('row_template.html',name=row[0],value=row[1],color=row[2],date_string=row[3])
	return response


def get_lymanfx_balance(account):
	if 'lymanfx' in account:
		lymanfx_percent = account['lymanfx']/account['deposit']
		return account['lymanfx'], lymanfx_percent * account['balance'], lymanfx_percent * account['equity']
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
				'<!-- <h1>UNDER CONSTRUCTION</h1><p>(moving money around, updating accounting, etc.)</p> -->'
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
				accounts[i]['last_update'] = datetime.now(timezone('US/Mountain'))
				joblib.dump(accounts[i], str(accounts[i]['account_id'])+'.pkl')
				return 'successful'
	else:
		return 'fail.'


#if __name__ == "__main__":
#	print('Starting web server...')
#	app.run(debug=False,host='0.0.0.0',port=80)
