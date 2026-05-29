from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/api/levels')
def get_levels():
    try:
        gld = yf.Ticker("GLD")
        chain = gld.option_chain(gld.options[0])
        calls = chain.calls[['strike', 'openInterest']]
        puts = chain.puts[['strike', 'openInterest']]
        
        # 1. Расчет Max Pain
        all_strikes = sorted(list(set(calls['strike']) | set(puts['strike'])))
        max_pain = 0
        min_loss = float('inf')
        for s in all_strikes:
            loss = sum(calls[calls['strike'] > s]['openInterest'] * (calls[calls['strike'] > s]['strike'] - s)) + \
                   sum(puts[puts['strike'] < s]['openInterest'] * (s - puts[puts['strike'] < s]['strike']))
            if loss < min_loss:
                min_loss = loss
                max_pain = s

        # 2. Формируем JSON с ТОП-10 уровней (фильтр OI > 500)
        levels = [{"price": round(float(max_pain) * 10.0, 2), "type": "max_pain", "oi": 0}]
        
        significant_calls = calls[calls['openInterest'] > 500].nlargest(10, 'openInterest')
        significant_puts = puts[puts['openInterest'] > 500].nlargest(10, 'openInterest')
        
        for _, r in significant_calls.iterrows():
            levels.append({"price": round(float(r.strike) * 10.0, 2), "type": "call", "oi": int(r.openInterest)})
        for _, r in significant_puts.iterrows():
            levels.append({"price": round(float(r.strike) * 10.0, 2), "type": "put", "oi": int(r.openInterest)})
            
        return jsonify(levels)
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    app.run()
