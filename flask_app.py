from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/api/levels')
def get_levels():
    try:
        # Получаем данные по GLD (золотой ETF)
        gld = yf.Ticker("GLD")
        chain = gld.option_chain(gld.options[0])
        
        # 1. Считаем Max Pain (точка минимальной боли для покупателей опционов)
        # Сумма (OI * разница цены)
        calls = chain.calls[['strike', 'openInterest']]
        puts = chain.puts[['strike', 'openInterest']]
        
        # Упрощенная логика Max Pain для примера
        max_pain = 0
        min_loss = float('inf')
        for strike in calls['strike']:
            loss = sum(calls['openInterest'] * [max(0, c - strike) for c in calls['strike']]) + \
                   sum(puts['openInterest'] * [max(0, strike - p) for p in puts['strike']])
            if loss < min_loss:
                min_loss = loss
                max_pain = strike

        # 2. Формируем список для MT5
        levels = []
        # Добавляем Max Pain
        levels.append({"price": round(max_pain * 10.0, 2), "type": "max_pain", "oi": 0})
        
        # Добавляем топ-3 уровня поддержки/сопротивления
        for _, r in calls.nlargest(3, 'openInterest').iterrows():
            levels.append({"price": round(r.strike * 10.0, 2), "type": "call", "oi": int(r.openInterest)})
        for _, r in puts.nlargest(3, 'openInterest').iterrows():
            levels.append({"price": round(r.strike * 10.0, 2), "type": "put", "oi": int(r.openInterest)})
            
        return jsonify(levels)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run()