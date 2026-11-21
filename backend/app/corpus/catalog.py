"""Product catalogue and French labels.

Each category has three representative *product types* (not brands): the panel records
which one a buyer chose, so product-level shares, prices and age profiles are computed from
the same simulated data as everything else. `query` is the image-search query used by
`scripts/fetch_images.py`.

Fields: key, English name, French name, image query, typical price (EUR),
trend ("rising" | "steady" | "cooling"), age skew (-1 younger ... +1 older), weight.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.corpus.spec import BY_SLUG, CATEGORIES


@dataclass(frozen=True)
class Product:
    key: str
    category: str
    name: str
    name_fr: str
    query: str
    price: float
    trend: str
    age_skew: float
    weight: float

    @property
    def per_month(self) -> bool:
        return self.key in MONTHLY

    @property
    def slug(self) -> str:
        return f"{self.category}--{self.key}"


MONTHLY = {
    "ev-lease",
    "delivery-pass",
    "student-plan",
    "individual-plan",
    "family-plan",
    "ad-supported-plan",
    "premium-plan",
    "streaming-bundle",
    "game-subscription",
    "budget-gym",
    "boutique-studio",
    "meditation-app",
    "journaling-app",
    "therapy-app",
    "ride-pass",
    "language-app",
    "ai-tutor",
    "etf-plan",
}

_P = dict[str, list[tuple[str, str, str, str, float, str, float, float]]]

RAW: _P = {
    "skincare": [
        (
            "vitamin-c-serum",
            "Vitamin C serum",
            "Sérum vitamine C",
            "serum bottle dropper skincare",
            24,
            "rising",
            0.2,
            1.0,
        ),
        ("spf-50-fluid", "SPF 50 daily fluid", "Fluide SPF 50 quotidien", "sunscreen bottle", 18, "rising", 0.1, 1.1),
        (
            "barrier-cream",
            "Ceramide barrier cream",
            "Crème barrière aux céramides",
            "face cream jar",
            16,
            "steady",
            0.0,
            0.9,
        ),
    ],
    "color-cosmetics": [
        ("lip-tint", "Lip tint", "Teinte à lèvres", "lipstick makeup", 12, "rising", -0.4, 1.2),
        (
            "skin-tint",
            "Skin tint foundation",
            "Fond de teint léger",
            "makeup",
            22,
            "steady",
            0.2,
            0.9,
        ),
        ("cream-blush", "Cream blush", "Blush crème", "makeup blush palette", 14, "rising", -0.2, 0.8),
    ],
    "fragrance": [
        ("eau-de-parfum", "Eau de parfum", "Eau de parfum", "perfume bottle", 65, "steady", 0.4, 0.9),
        ("body-mist", "Body mist", "Brume parfumée", "woman perfume", 14, "rising", -0.5, 1.2),
        (
            "discovery-set",
            "Fragrance discovery set",
            "Coffret découverte parfums",
            "perfume bottles collection",
            30,
            "rising",
            0.0,
            0.7,
        ),
    ],
    "haircare": [
        (
            "bond-repair",
            "Bond repair treatment",
            "Soin réparateur de liaisons",
            "hair care products",
            28,
            "rising",
            0.2,
            0.8,
        ),
        ("scalp-serum", "Scalp serum", "Sérum cuir chevelu", "hair oil bottle", 22, "rising", 0.1, 0.7),
        ("everyday-shampoo", "Everyday shampoo", "Shampooing quotidien", "shampoo bottles", 6, "steady", 0.0, 1.4),
    ],
    "mens-grooming": [
        ("beard-oil", "Beard oil", "Huile à barbe", "beard grooming man", 15, "steady", 0.4, 0.8),
        (
            "men-moisturiser",
            "Oil-control moisturiser",
            "Hydratant matifiant",
            "man shaving mirror",
            14,
            "rising",
            0.0,
            1.0,
        ),
        (
            "electric-trimmer",
            "Electric trimmer",
            "Tondeuse électrique",
            "electric razor shaver",
            45,
            "steady",
            0.1,
            0.8,
        ),
    ],
    "nail-care": [
        ("press-on-nails", "Press-on nails", "Faux ongles adhésifs", "manicure nails", 12, "rising", -0.4, 1.1),
        ("gel-kit", "At-home gel kit", "Kit gel maison", "nail polish bottles", 35, "steady", 0.2, 0.7),
        ("nail-polish", "Nail polish", "Vernis à ongles", "nail polish colors", 8, "cooling", 0.0, 0.9),
    ],
    "fast-fashion": [
        ("graphic-tee", "Graphic T-shirt", "T-shirt imprimé", "t-shirt clothing rack", 15, "steady", -0.3, 1.2),
        ("wide-leg-jeans", "Wide-leg jeans", "Jean large", "denim jeans", 35, "rising", 0.0, 1.0),
        ("going-out-top", "Going-out top", "Haut de soirée", "fashion clothing store", 20, "cooling", -0.2, 0.8),
    ],
    "secondhand-fashion": [
        ("vintage-jacket", "Vintage jacket", "Veste vintage", "vintage clothing store", 40, "rising", 0.1, 1.0),
        ("thrifted-denim", "Thrifted denim", "Denim de seconde main", "thrift store clothes", 22, "rising", -0.1, 1.1),
        (
            "preloved-designer",
            "Pre-loved designer piece",
            "Pièce de créateur d'occasion",
            "luxury handbag",
            120,
            "steady",
            0.5,
            0.5,
        ),
    ],
    "sneakers": [
        ("running-shoe", "Everyday running shoe", "Chaussure de running", "running shoes", 110, "rising", 0.2, 1.1),
        ("terrace-sneaker", "Terrace sneaker", "Sneaker rétro", "sneakers shoes", 95, "rising", -0.1, 1.0),
        ("limited-drop", "Limited-edition drop", "Édition limitée", "sneaker collection", 180, "cooling", -0.2, 0.5),
    ],
    "athleisure": [
        ("leggings", "Performance leggings", "Legging de sport", "yoga leggings", 45, "steady", 0.1, 1.2),
        ("oversized-hoodie", "Oversized hoodie", "Sweat à capuche oversize", "hoodie", 50, "steady", -0.2, 1.0),
        ("run-club-shorts", "Running shorts", "Short de course", "running athlete", 30, "rising", 0.2, 0.7),
    ],
    "demi-fine-jewelry": [
        ("gold-hoops", "Gold vermeil hoops", "Créoles en vermeil", "gold earrings jewelry", 45, "rising", 0.2, 1.1),
        ("layered-necklace", "Layered necklace", "Collier superposé", "gold necklace", 55, "steady", 0.1, 0.9),
        ("stacking-rings", "Stacking rings", "Bagues empilables", "rings jewelry", 35, "rising", -0.1, 0.8),
    ],
    "bags-accessories": [
        ("tote-bag", "Canvas tote bag", "Tote bag en toile", "tote bag", 25, "steady", 0.0, 1.1),
        ("shoulder-bag", "Shoulder bag", "Sac porté épaule", "handbag fashion", 60, "rising", 0.2, 0.9),
        ("backpack", "Everyday backpack", "Sac à dos", "backpack", 55, "steady", -0.3, 1.0),
    ],
    "eyewear": [
        ("statement-frames", "Statement frames", "Montures affirmées", "eyeglasses frames", 120, "rising", 0.3, 0.9),
        ("sunglasses", "Sunglasses", "Lunettes de soleil", "sunglasses", 60, "steady", -0.1, 1.1),
        ("contact-lenses", "Monthly contact lenses", "Lentilles mensuelles", "contact lens", 25, "steady", 0.4, 0.6),
    ],
    "energy-drinks": [
        (
            "zero-sugar-can",
            "Zero-sugar energy can",
            "Canette énergisante sans sucre",
            "energy drink can",
            2,
            "rising",
            -0.1,
            1.3,
        ),
        (
            "creator-brand-drink",
            "Creator-brand energy drink",
            "Boisson de marque créateur",
            "colorful drink cans",
            3,
            "rising",
            -0.5,
            0.8,
        ),
        (
            "classic-energy",
            "Classic energy drink",
            "Boisson énergisante classique",
            "energy drink",
            2,
            "cooling",
            0.2,
            0.9,
        ),
    ],
    "plant-based-food": [
        ("oat-milk", "Oat milk", "Lait d'avoine", "oat milk carton", 2, "steady", 0.2, 1.3),
        ("tofu", "Tofu", "Tofu", "tofu", 3, "rising", 0.3, 0.8),
        ("plant-burger", "Plant-based burger", "Burger végétal", "veggie burger", 5, "cooling", 0.0, 0.8),
    ],
    "specialty-coffee": [
        ("iced-latte", "Iced latte", "Latte glacé", "iced coffee", 5, "rising", 0.0, 1.2),
        ("matcha-latte", "Matcha latte", "Matcha latte", "matcha latte", 5, "rising", -0.1, 1.0),
        (
            "coffee-beans",
            "Specialty coffee beans",
            "Café de spécialité en grains",
            "coffee beans bag",
            14,
            "steady",
            0.6,
            0.6,
        ),
    ],
    "better-for-you-snacks": [
        ("protein-bar", "Protein bar", "Barre protéinée", "protein bar", 2, "rising", 0.1, 1.2),
        ("rice-cakes", "Flavoured rice cakes", "Galettes de riz", "rice cakes snack", 2, "steady", 0.0, 0.8),
        (
            "high-protein-yogurt",
            "High-protein yogurt",
            "Yaourt riche en protéines",
            "yogurt bowl",
            2,
            "rising",
            0.2,
            1.0,
        ),
    ],
    "low-no-alcohol": [
        ("na-beer", "Alcohol-free beer", "Bière sans alcool", "beer bottles", 2, "rising", 0.3, 1.2),
        ("mocktail", "Bar mocktail", "Mocktail", "mocktail drink", 9, "rising", 0.0, 1.0),
        ("na-spirit", "Non-alcoholic spirit", "Spiritueux sans alcool", "cocktail glass", 25, "steady", 0.5, 0.5),
    ],
    "food-delivery": [
        ("burger-order", "Burger delivery", "Burger livré", "burger fries", 15, "steady", -0.2, 1.2),
        ("sushi-order", "Sushi delivery", "Sushis livrés", "sushi", 22, "steady", 0.3, 0.9),
        (
            "delivery-pass",
            "Delivery subscription pass",
            "Abonnement livraison",
            "food delivery bike",
            6,
            "rising",
            0.4,
            0.6,
        ),
    ],
    "functional-beverages": [
        (
            "electrolyte-mix",
            "Electrolyte drink mix",
            "Boisson électrolytes",
            "sports drink bottle",
            3,
            "rising",
            0.0,
            1.0,
        ),
        ("prebiotic-soda", "Prebiotic soda", "Soda prébiotique", "soda can", 3, "rising", 0.1, 0.9),
        ("kombucha", "Kombucha", "Kombucha", "kombucha", 4, "steady", 0.4, 0.8),
    ],
    "smartphones": [
        ("flagship-phone", "Flagship smartphone", "Smartphone haut de gamme", "smartphone", 950, "steady", 0.2, 1.0),
        (
            "refurbished-phone",
            "Refurbished smartphone",
            "Smartphone reconditionné",
            "mobile phone hand",
            420,
            "rising",
            0.1,
            1.0,
        ),
        (
            "midrange-phone",
            "Mid-range smartphone",
            "Smartphone milieu de gamme",
            "phone on table",
            350,
            "steady",
            -0.2,
            0.9,
        ),
    ],
    "wireless-audio": [
        (
            "over-ear-headphones",
            "Over-ear headphones",
            "Casque circum-auriculaire",
            "headphones",
            180,
            "rising",
            0.0,
            1.0,
        ),
        (
            "true-wireless-earbuds",
            "True wireless earbuds",
            "Écouteurs sans fil",
            "wireless earbuds",
            80,
            "steady",
            -0.1,
            1.2,
        ),
        ("portable-speaker", "Portable speaker", "Enceinte portable", "bluetooth speaker", 70, "steady", -0.2, 0.7),
    ],
    "gaming-hardware": [
        ("console", "Home console", "Console de salon", "game console controller", 450, "steady", -0.1, 1.0),
        ("handheld-pc", "Handheld gaming PC", "PC portable de jeu", "handheld gaming", 550, "rising", 0.1, 0.6),
        (
            "mechanical-keyboard",
            "Mechanical keyboard",
            "Clavier mécanique",
            "mechanical keyboard",
            110,
            "rising",
            0.0,
            0.9,
        ),
    ],
    "wearables": [
        ("smartwatch", "Smartwatch", "Montre connectée", "smartwatch", 280, "steady", 0.2, 1.1),
        ("smart-ring", "Smart ring", "Bague connectée", "ring hand", 300, "rising", 0.5, 0.5),
        ("fitness-band", "Fitness band", "Bracelet d'activité", "fitness watch running", 60, "cooling", -0.1, 0.9),
    ],
    "creator-gear": [
        (
            "compact-camera",
            "Compact digital camera",
            "Appareil photo compact",
            "compact camera",
            300,
            "rising",
            -0.2,
            0.9,
        ),
        ("wireless-mic", "Wireless microphone", "Micro sans fil", "microphone", 150, "rising", 0.1, 1.0),
        ("ring-light", "Ring light", "Anneau lumineux", "ring light studio", 40, "cooling", -0.3, 0.8),
    ],
    "smart-home": [
        ("led-strip", "LED light strip", "Ruban LED", "led lights room", 25, "steady", -0.4, 1.2),
        ("smart-speaker", "Smart speaker", "Enceinte connectée", "smart speaker", 60, "cooling", 0.3, 0.8),
        ("sunrise-alarm", "Sunrise alarm clock", "Réveil lumière", "alarm clock bedside", 50, "rising", 0.3, 0.6),
    ],
    "music-streaming": [
        ("student-plan", "Student plan", "Abonnement étudiant", "headphones music phone", 6, "steady", -0.4, 1.2),
        ("individual-plan", "Individual plan", "Abonnement individuel", "music streaming", 11, "steady", 0.3, 1.0),
        (
            "family-plan",
            "Family / duo plan",
            "Abonnement famille / duo",
            "friends listening music",
            17,
            "rising",
            0.2,
            0.6,
        ),
    ],
    "video-streaming": [
        ("ad-supported-plan", "Ad-supported plan", "Offre avec publicités", "watching tv couch", 7, "rising", 0.0, 1.1),
        ("premium-plan", "Premium plan", "Offre premium", "television screen", 18, "cooling", 0.3, 0.8),
        ("streaming-bundle", "Streaming bundle", "Bouquet de streaming", "remote control tv", 22, "rising", 0.4, 0.6),
    ],
    "mobile-gaming": [
        ("battle-pass", "Battle pass", "Passe de combat", "mobile gaming phone", 10, "steady", -0.3, 1.1),
        ("cosmetic-skin", "Cosmetic skin", "Skin cosmétique", "gamer playing", 8, "rising", -0.4, 1.0),
        ("game-subscription", "Game subscription", "Abonnement de jeux", "video games", 6, "steady", 0.2, 0.6),
    ],
    "live-events": [
        (
            "concert-ticket",
            "Stadium concert ticket",
            "Billet de concert en stade",
            "concert crowd",
            95,
            "rising",
            0.1,
            1.2,
        ),
        ("festival-pass", "Festival pass", "Pass festival", "music festival", 220, "steady", 0.2, 0.7),
        ("club-night", "Club night", "Soirée en club", "nightclub dj", 20, "cooling", 0.0, 0.8),
    ],
    "books": [
        ("special-edition", "Special-edition novel", "Roman édition collector", "books stack", 25, "rising", -0.2, 1.0),
        ("paperback", "Paperback novel", "Roman de poche", "reading book", 10, "steady", 0.0, 1.2),
        ("e-reader", "E-reader", "Liseuse", "e-reader", 130, "steady", 0.5, 0.4),
    ],
    "collectibles": [
        ("blind-box", "Blind-box figure", "Figurine surprise", "toy figures", 15, "rising", -0.2, 1.1),
        ("trading-cards", "Trading card booster", "Booster de cartes", "trading cards", 6, "rising", -0.3, 1.0),
        ("vinyl-figure", "Vinyl figure", "Figurine vinyle", "collectible figure", 18, "steady", 0.2, 0.7),
    ],
    "travel-experiences": [
        ("city-break", "European city break", "City break en Europe", "city travel", 350, "rising", 0.3, 1.1),
        ("hostel-trip", "Hostel backpacking trip", "Voyage en auberge", "backpacker travel", 250, "steady", -0.3, 0.9),
        ("beach-holiday", "Beach holiday", "Vacances à la plage", "beach holiday", 600, "steady", 0.4, 0.8),
    ],
    "gym-fitness": [
        ("budget-gym", "Budget gym membership", "Abonnement salle low-cost", "gym weights", 25, "rising", 0.0, 1.3),
        ("pilates-class", "Pilates class pack", "Carnet de cours de Pilates", "pilates", 120, "rising", 0.4, 0.6),
        (
            "boutique-studio",
            "Boutique studio membership",
            "Abonnement studio boutique",
            "fitness class",
            90,
            "steady",
            0.3,
            0.5,
        ),
    ],
    "supplements": [
        ("creatine", "Creatine", "Créatine", "supplement powder scoop", 25, "rising", 0.0, 1.0),
        ("magnesium", "Magnesium", "Magnésium", "vitamin pills", 15, "rising", 0.3, 0.9),
        ("protein-powder", "Protein powder", "Protéine en poudre", "protein shake", 35, "steady", -0.1, 1.1),
    ],
    "mental-wellness-apps": [
        ("meditation-app", "Meditation app", "Application de méditation", "meditation", 10, "steady", 0.2, 1.0),
        ("journaling-app", "Journaling app", "Application de journal", "journal writing", 6, "rising", -0.1, 0.9),
        ("therapy-app", "Online therapy", "Thérapie en ligne", "laptop video call", 60, "rising", 0.5, 0.5),
    ],
    "sleep-products": [
        ("sleep-mask", "Silk sleep mask", "Masque de sommeil en soie", "sleeping mask", 20, "rising", 0.0, 1.0),
        ("magnesium-drink", "Magnesium night drink", "Boisson magnésium du soir", "night tea", 18, "rising", 0.2, 0.8),
        ("mouth-tape", "Mouth tape", "Bande buccale", "bedroom bed", 12, "cooling", -0.1, 0.6),
    ],
    "period-care": [
        ("period-underwear", "Period underwear", "Culotte menstruelle", "underwear cotton", 30, "rising", 0.4, 0.9),
        ("menstrual-cup", "Menstrual cup", "Coupe menstruelle", "menstrual cup", 22, "steady", 0.3, 0.6),
        ("organic-tampons", "Organic tampons", "Tampons bio", "cotton pads", 5, "steady", -0.2, 1.2),
    ],
    "oral-care": [
        ("whitening-strips", "Whitening strips", "Bandes blanchissantes", "smile teeth", 30, "rising", 0.0, 0.9),
        (
            "electric-toothbrush",
            "Electric toothbrush",
            "Brosse à dents électrique",
            "electric toothbrush",
            60,
            "steady",
            0.3,
            1.0,
        ),
        (
            "purple-toothpaste",
            "Colour-corrector toothpaste",
            "Dentifrice correcteur",
            "toothpaste",
            12,
            "cooling",
            -0.4,
            0.7,
        ),
    ],
    "home-decor": [
        ("poster-print", "Poster print", "Affiche décorative", "posters wall decor", 20, "steady", -0.2, 1.1),
        ("mirror", "Statement mirror", "Miroir décoratif", "mirror interior", 70, "rising", 0.3, 0.7),
        ("throw-blanket", "Throw blanket", "Plaid", "blanket", 35, "steady", 0.2, 0.9),
    ],
    "houseplants": [
        ("pothos", "Pothos", "Pothos", "houseplant pot", 15, "steady", 0.2, 1.1),
        ("monstera", "Monstera", "Monstera", "monstera plant", 35, "cooling", 0.3, 0.7),
        ("succulent-set", "Succulent set", "Lot de succulentes", "succulents", 18, "steady", -0.2, 0.9),
    ],
    "candles-home-fragrance": [
        ("scented-candle", "Scented candle", "Bougie parfumée", "scented candle", 22, "steady", 0.1, 1.3),
        ("reed-diffuser", "Reed diffuser", "Diffuseur à bâtonnets", "reed diffuser", 28, "rising", 0.4, 0.7),
        ("room-spray", "Room spray", "Spray d'ambiance", "aromatherapy", 12, "steady", -0.1, 0.7),
    ],
    "small-appliances": [
        ("air-fryer", "Air fryer", "Friteuse à air", "kitchen appliance", 90, "steady", 0.4, 1.2),
        ("portable-blender", "Portable blender", "Blender portable", "smoothie blender", 35, "rising", -0.2, 0.9),
        ("espresso-machine", "Espresso machine", "Machine à espresso", "espresso machine", 180, "rising", 0.5, 0.6),
    ],
    "furniture": [
        ("modular-shelf", "Modular shelving", "Étagère modulable", "bookshelf interior", 80, "rising", 0.3, 0.9),
        ("desk-setup", "Home-office desk", "Bureau télétravail", "desk setup", 150, "steady", 0.3, 0.8),
        ("secondhand-armchair", "Second-hand armchair", "Fauteuil d'occasion", "armchair", 90, "rising", 0.4, 0.7),
    ],
    "electric-vehicles": [
        ("city-ev", "Compact city EV", "Citadine électrique", "electric car", 24000, "rising", 0.6, 1.1),
        ("ev-suv", "Electric crossover", "SUV électrique", "electric suv car", 42000, "steady", 0.8, 0.6),
        (
            "ev-lease",
            "Social leasing EV",
            "Location sociale électrique",
            "car charging station",
            100,
            "rising",
            0.5,
            0.9,
        ),
    ],
    "used-cars": [
        (
            "small-hatchback",
            "Used small hatchback",
            "Petite citadine d'occasion",
            "small car street",
            9000,
            "steady",
            0.4,
            1.3,
        ),
        ("used-hybrid", "Used hybrid", "Hybride d'occasion", "car parked", 16000, "rising", 0.8, 0.7),
        ("classic-car", "Vintage / classic car", "Voiture ancienne", "vintage car", 12000, "cooling", 0.3, 0.3),
    ],
    "ride-hailing": [
        ("night-ride", "Late-night ride", "Course de nuit", "city taxi night", 18, "steady", 0.0, 1.2),
        ("airport-ride", "Airport transfer", "Trajet aéroport", "airport", 45, "steady", 0.6, 0.6),
        ("ride-pass", "Ride subscription pass", "Abonnement VTC", "car interior", 10, "rising", 0.5, 0.5),
    ],
    "micromobility": [
        ("shared-ebike", "Shared e-bike", "Vélo électrique partagé", "bike sharing city", 15, "rising", 0.2, 1.2),
        ("e-scooter", "E-scooter", "Trottinette électrique", "electric scooter", 450, "cooling", -0.3, 0.8),
        ("own-ebike", "Personal e-bike", "Vélo électrique personnel", "electric bicycle", 1200, "rising", 0.7, 0.5),
    ],
    "bnpl": [
        ("pay-in-3", "Pay in 3", "Paiement en 3 fois", "online shopping card", 120, "steady", 0.0, 1.3),
        ("pay-in-30-days", "Pay in 30 days", "Paiement à 30 jours", "shopping bags", 60, "cooling", -0.2, 0.8),
        ("financing-plan", "Long financing plan", "Financement long", "credit card laptop", 600, "rising", 0.6, 0.4),
    ],
    "investing-apps": [
        ("etf-plan", "ETF savings plan", "Plan d'épargne ETF", "stock market chart", 80, "rising", 0.6, 1.1),
        (
            "fractional-shares",
            "Fractional shares",
            "Actions fractionnées",
            "trading screen",
            50,
            "steady",
            0.1,
            0.9,
        ),
        ("crypto-app", "Crypto app", "Application crypto", "bitcoin", 60, "cooling", -0.1, 0.7),
    ],
    "pet-care": [
        (
            "fresh-pet-food",
            "Fresh pet food",
            "Nourriture fraîche pour animaux",
            "dog food bowl",
            70,
            "rising",
            0.5,
            0.8,
        ),
        (
            "cat-toys",
            "Cat toys & accessories",
            "Jouets et accessoires pour chat",
            "cat playing",
            15,
            "steady",
            0.0,
            1.0,
        ),
        ("dog-walk-gear", "Dog walking gear", "Équipement de promenade", "dog leash walk", 30, "steady", 0.3, 0.9),
    ],
    "online-learning": [
        (
            "language-app",
            "Language learning app",
            "Application de langues",
            "language learning",
            12,
            "steady",
            -0.1,
            1.2,
        ),
        ("coding-course", "Coding course", "Formation au code", "coding laptop", 40, "rising", 0.5, 0.8),
        ("ai-tutor", "AI tutor", "Tuteur IA", "student studying", 15, "rising", 0.0, 0.7),
    ],
}

PRODUCTS: list[Product] = [
    Product(key, cat, name, fr, query, float(price), trend, skew, weight)
    for cat, items in RAW.items()
    for (key, name, fr, query, price, trend, skew, weight) in items
]
BY_CATEGORY: dict[str, list[Product]] = {}
for _p in PRODUCTS:
    BY_CATEGORY.setdefault(_p.category, []).append(_p)
PRODUCT_BY_SLUG: dict[str, Product] = {p.slug: p for p in PRODUCTS}

GROUPS_FR = {
    "beauty": "Beauté & soins",
    "fashion": "Mode & accessoires",
    "food": "Alimentation & boissons",
    "tech": "Tech & électronique",
    "entertainment": "Divertissement & expériences",
    "wellness": "Santé & bien-être",
    "home": "Maison & déco",
    "mobility": "Voitures & mobilité",
    "services": "Argent & services",
}

CATEGORY_FR = {
    "skincare": "Soins du visage",
    "color-cosmetics": "Maquillage",
    "fragrance": "Parfums",
    "haircare": "Soins capillaires",
    "mens-grooming": "Soins pour hommes",
    "nail-care": "Ongles",
    "fast-fashion": "Fast fashion",
    "secondhand-fashion": "Mode de seconde main",
    "sneakers": "Sneakers",
    "athleisure": "Sportswear",
    "demi-fine-jewelry": "Bijoux demi-fins",
    "bags-accessories": "Sacs & accessoires",
    "eyewear": "Lunettes",
    "energy-drinks": "Boissons énergisantes",
    "plant-based-food": "Alimentation végétale",
    "specialty-coffee": "Café de spécialité",
    "better-for-you-snacks": "Snacks sains",
    "low-no-alcohol": "Boissons sans alcool",
    "food-delivery": "Livraison de repas",
    "functional-beverages": "Boissons fonctionnelles",
    "smartphones": "Smartphones",
    "wireless-audio": "Audio sans fil",
    "gaming-hardware": "Matériel gaming",
    "wearables": "Objets connectés",
    "creator-gear": "Matériel de créateur",
    "smart-home": "Maison connectée",
    "music-streaming": "Streaming musical",
    "video-streaming": "Streaming vidéo",
    "mobile-gaming": "Jeux mobiles",
    "live-events": "Concerts & événements",
    "books": "Livres",
    "collectibles": "Objets de collection",
    "travel-experiences": "Voyages",
    "gym-fitness": "Salles de sport",
    "supplements": "Compléments alimentaires",
    "mental-wellness-apps": "Applis bien-être mental",
    "sleep-products": "Sommeil",
    "period-care": "Protections menstruelles",
    "oral-care": "Hygiène bucco-dentaire",
    "home-decor": "Décoration",
    "houseplants": "Plantes d'intérieur",
    "candles-home-fragrance": "Bougies & parfums d'intérieur",
    "small-appliances": "Petit électroménager",
    "furniture": "Mobilier",
    "electric-vehicles": "Voitures électriques",
    "used-cars": "Voitures d'occasion",
    "ride-hailing": "VTC",
    "micromobility": "Micromobilité",
    "bnpl": "Paiement fractionné",
    "investing-apps": "Applis d'investissement",
    "pet-care": "Animaux de compagnie",
    "online-learning": "Formation en ligne",
}

assert set(RAW) == set(BY_SLUG), set(BY_SLUG) ^ set(RAW)
assert set(CATEGORY_FR) == set(BY_SLUG), set(BY_SLUG) ^ set(CATEGORY_FR)
assert all(len(v) == 3 for v in RAW.values())
assert len(PRODUCT_BY_SLUG) == len(PRODUCTS) == 3 * len(CATEGORIES)
