from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import random
import io
from reportlab.pdfgen import canvas  # Remove this line if not used
from PyPDF2 import PdfReader, PdfWriter, PdfMerger  # Remove this line if not used
from reportlab.lib.pagesizes import letter  # Remove this line if not used
import os  # Remove this line if not used

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    ac = db.Column(db.Integer, nullable=True)
    hp = db.Column(db.Integer, nullable=True)

def calculate_modifier(score):
    modifier = (score - 10) // 2
    return modifier if modifier <= 0 else f"+{modifier}"

def roll_stat():
    rolls = [random.randint(1, 6) for _ in range(4)]
    return sum(sorted(rolls)[1:])  # Drop lowest die

def calculate_hp(con_mod, hit_die, level=1):
    # Calculate HP based on level and hit die
    if level == 1:
        initial_hp = hit_die  # Max roll for level 1
    else:
        initial_hp = sum(random.randint(1, hit_die) for _ in range(level - 1)) + hit_die  # Max roll for level 1 plus additional rolls
    initial_hp += con_mod
    return initial_hp

def calculate_ac(dex_mod):
    # Base AC for a non-armored character is 10 + Dexterity modifier
    return 10 + dex_mod  # Removed the min(10, ...) constraint

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-stats', methods=['POST'])
def generate_stats():
    data = request.json
    character_class = data.get('class', 'Fighter')  # Default to Fighter if no class is selected
    
    # Determine hit die based on class
    hit_die_dict = {
        'Barbarian': 12,
        'Fighter': 10,
        'Paladin': 10,
        'Ranger': 10,
        'Artificer': 8,
        'Bard': 8,
        'Cleric': 8,
        'Druid': 8,
        'Monk': 8,
        'Rogue': 8,
        'Warlock': 8,
        'Sorcerer': 6,
        'Wizard': 6
    }
    
    hit_die = hit_die_dict.get(character_class, 10)  # Default to 10 if class is not recognized
    
    stats = {
        'Strength': roll_stat(),
        'Dexterity': roll_stat(),
        'Constitution': roll_stat(),
        'Intelligence': roll_stat(),
        'Wisdom': roll_stat(),
        'Charisma': roll_stat()
    }
    
    modifiers = {stat: calculate_modifier(score) for stat, score in stats.items()}
    
    # Calculate AC and HP
    ac = calculate_ac(int(modifiers['Dexterity'].lstrip('+')) if isinstance(modifiers['Dexterity'], str) else modifiers['Dexterity'])
    hp = calculate_hp(int(modifiers['Constitution'].lstrip('+')) if isinstance(modifiers['Constitution'], str) else modifiers['Constitution'], hit_die)
    
    # Create character information
    character_info = f"**Character Class**: {character_class}\n"
    character_info += "**Stats**:\n"
    for stat, value in stats.items():
        character_info += f"  - {stat}: {value} ({modifiers[stat]})\n"
    character_info += f"**AC**: {ac}\n"
    character_info += f"**HP**: {hp}\n"
    
    return jsonify({
        'stats': stats,
        'modifiers': modifiers,
        'ac': ac,
        'hp': hp,
        'character_info': character_info
    })

@app.route('/get-notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify({'notes': [{'id': note.id, 'content': note.content, 'ac': note.ac, 'hp': note.hp} for note in notes]})

@app.route('/download-notes', methods=['POST'])
def download_notes():
    data = request.json
    note_content = data.get('content', '')
    
    # Create a BytesIO buffer for the text file
    text_buffer = io.BytesIO()
    text_buffer.write(note_content.encode('utf-8'))
    text_buffer.seek(0)
    
    return send_file(text_buffer, as_attachment=True, download_name='character_notes.txt')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
