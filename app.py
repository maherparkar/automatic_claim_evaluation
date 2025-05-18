from portal import create_app

app = create_app()

if __name__ == "__main__":
    # app.run(host="192.168.29.207")
    app.run(debug=False, port=7006)
