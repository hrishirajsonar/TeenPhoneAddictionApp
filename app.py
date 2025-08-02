from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-1234567890'  # Replace with a secure key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model for database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Form for CSV upload
class UploadForm(FlaskForm):
    file = FileField('Upload CSV File')
    submit = SubmitField('Upload')

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

def clean_data(df):
    text_cols = df.select_dtypes(include=['object']).columns
    for col in text_cols:
        df[col] = df[col].str.strip()
        if col not in ['Name', 'Phone_Usage_Purpose', 'Location', 'Gender']:
            df[col] = df[col].str.lower()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mode()[0])
    return df

def generate_summary(df):
    nums = df.select_dtypes(include=[np.number])
    return {
        'mean': nums.mean(),
        'median': nums.median(),
        'mode': nums.mode().iloc[0],
        'correlation': nums.corr()
    }

def filter_data(df, gender, grade):
    out = df.copy()
    if gender:
        out = out[out['Gender'] == gender]
    if grade:
        out = out[out['School_Grade'] == grade]
    return out

def generate_chart(title, func, **kwargs):
    img = io.BytesIO()
    plt.figure()
    func(**kwargs)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

@app.route('/')
def home():
    return render_template('home.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Sign-up successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('analysis', filename=filename))
        else:
            flash('Please upload a valid CSV file.', 'error')
    return render_template('upload.html', form=form)

@app.route('/analysis/<filename>')
@login_required
def analysis(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        df = pd.read_csv(file_path)
        df = clean_data(df)
        gender = request.args.get('gender')
        grade = request.args.get('school_grade')
        filtered_df = filter_data(df, gender, grade)
        summary = generate_summary(filtered_df)

        # Amanda's Charts
        charts = {
            'hist_daily_usage': generate_chart(
                "Distribution of Daily Phone Usage Hours",
                sns.histplot, data=filtered_df, x="Daily_Usage_Hours", bins=20, kde=True
            ),
            'scatter_usage_vs_perf': generate_chart(
                "Daily Phone Usage vs Academic Performance",
                sns.regplot, x="Daily_Usage_Hours", y="Academic_Performance", data=filtered_df,
                scatter_kws={"s": 15, "alpha": 0.6}, line_kws={"label": "Linear Fit"}
            ),
            'bar_addiction_by_purpose': generate_chart(
                "Average Addiction Level by Phone Usage Purpose",
                lambda **k: filtered_df.groupby("Phone_Usage_Purpose")["Addiction_Level"].mean().sort_values(ascending=False).plot(kind="bar"),
                data=filtered_df
            ),
            'heatmap_correlations': generate_chart(
                "Correlation Matrix of Key Metrics",
                sns.heatmap, data=filtered_df[["Daily_Usage_Hours", "Sleep_Hours", "Academic_Performance", "Depression_Level", "Self_Esteem", "Addiction_Level"]].corr(),
                annot=True, fmt=".2f", cmap="viridis", cbar_kws={"label": "Correlation"}, square=True
            )
        }

        # Minnu's Charts
        charts.update({
            'bar_usage_by_grade': generate_chart(
                "Average Daily Phone Usage by School Grade",
                lambda **k: filtered_df.groupby("School_Grade")["Daily_Usage_Hours"].mean().sort_values().plot(kind="bar", color="skyblue"),
                data=filtered_df
            ),
            'line_sleep_vs_addiction': generate_chart(
                "Addiction Level vs Sleep Hours",
                sns.lineplot, data=filtered_df.sort_values("Sleep_Hours"), x="Sleep_Hours", y="Addiction_Level"
            ),
            'heatmap_correlation': generate_chart(
                "Correlation Heatmap",
                sns.heatmap, data=filtered_df.corr(numeric_only=True), cmap="coolwarm", annot=False
            ),
            'pie_usage_purpose': generate_chart(
                "Phone Usage Purpose Distribution",
                lambda **k: filtered_df["Phone_Usage_Purpose"].value_counts().plot.pie(autopct="%1.1f%%", startangle=140),
                data=filtered_df
            )
        })

        # Additional Charts
        charts.update({
            'box_perf_by_gender': generate_chart(
                "Distribution of Academic Performance by Gender",
                sns.boxplot, x="Gender", y="Academic_Performance", data=filtered_df
            ),
            'bar_sleep_by_grade': generate_chart(
                "Average Sleep Hours by School Grade",
                lambda **k: filtered_df.groupby("School_Grade")["Sleep_Hours"].mean().sort_values().plot(kind="bar", color="lightgreen"),
                data=filtered_df
            ),
            'scatter_exercise_vs_anxiety': generate_chart(
                "Exercise Hours vs Anxiety Level",
                sns.regplot, x="Exercise_Hours", y="Anxiety_Level", data=filtered_df,
                scatter_kws={"s": 15, "alpha": 0.6}
            ),
            'line_depression_vs_social': generate_chart(
                "Depression Level vs Social Interactions",
                sns.lineplot, data=filtered_df.sort_values("Social_Interactions"), x="Social_Interactions", y="Depression_Level"
            ),
            'pie_gender': generate_chart(
                "Gender Distribution",
                lambda **k: filtered_df["Gender"].value_counts().plot.pie(autopct="%1.1f%%", startangle=90),
                data=filtered_df
            ),
            'bar_screen_time_by_addiction': generate_chart(
                "Average Screen Time Before Bed by Addiction Level",
                lambda **k: filtered_df.groupby("Addiction_Level")["Screen_Time_Before_Bed"].mean().sort_values().plot(kind="bar", color="salmon"),
                data=filtered_df
            ),
            'heatmap_lifestyle': generate_chart(
                "Correlation of Lifestyle Factors",
                sns.heatmap, data=filtered_df[["Sleep_Hours", "Exercise_Hours", "Social_Interactions"]].corr(),
                annot=True, fmt=".2f", cmap="YlOrRd", cbar_kws={"label": "Correlation"}
            ),
            'box_usage_by_purpose': generate_chart(
                "Distribution of Daily Usage Hours by Phone Usage Purpose",
                sns.boxplot, x="Phone_Usage_Purpose", y="Daily_Usage_Hours", data=filtered_df
            )
        })

        return render_template('analysis.html', summary=summary, filename=filename, gender=gender, grade=grade, charts=charts)
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True)