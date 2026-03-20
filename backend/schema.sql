-- =============================================================
-- Yelp Clone — MySQL DDL
-- =============================================================

CREATE DATABASE IF NOT EXISTS yelp_clone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yelp_clone;

-- =============================================================
-- 1. users
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role            ENUM('user', 'owner') NOT NULL DEFAULT 'user',
    name            VARCHAR(120)  NOT NULL,
    email           VARCHAR(255)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    phone           VARCHAR(30)   DEFAULT NULL,
    about_me        TEXT          DEFAULT NULL,
    city            VARCHAR(100)  DEFAULT NULL,
    state           VARCHAR(100)  DEFAULT NULL,
    country         VARCHAR(100)  DEFAULT 'US',
    languages       JSON          DEFAULT NULL,  -- e.g. ["English","Spanish"]
    gender          VARCHAR(30)   DEFAULT NULL,
    profile_picture VARCHAR(512)  DEFAULT NULL,  -- URL or file path
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_users_email  (email),
    INDEX idx_users_role   (role),
    INDEX idx_users_city   (city)
) ENGINE=InnoDB;


-- =============================================================
-- 2. user_preferences
-- =============================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id                     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id                INT UNSIGNED NOT NULL UNIQUE,
    cuisine_preferences    JSON    DEFAULT NULL,  -- ["Italian","Sushi"]
    price_range            TINYINT UNSIGNED DEFAULT NULL,  -- 1-4 ($, $$, $$$, $$$$)
    preferred_locations    JSON    DEFAULT NULL,  -- ["San Francisco","Palo Alto"]
    search_radius          DECIMAL(6,2) DEFAULT 10.00,   -- miles
    dietary_needs          JSON    DEFAULT NULL,  -- ["vegan","gluten-free"]
    ambiance_preferences   JSON    DEFAULT NULL,  -- ["romantic","outdoor","family-friendly"]
    sort_preference        ENUM('rating','distance','price_asc','price_desc','most_reviewed')
                           NOT NULL DEFAULT 'rating',
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_pref_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_pref_user (user_id)
) ENGINE=InnoDB;


-- =============================================================
-- 3. restaurants
-- =============================================================
CREATE TABLE IF NOT EXISTS restaurants (
    id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    owner_id             INT UNSIGNED NOT NULL,   -- user with role='owner'
    added_by             INT UNSIGNED NOT NULL,   -- user who submitted the listing
    name                 VARCHAR(255) NOT NULL,
    cuisine_type         VARCHAR(100) DEFAULT NULL,
    description          TEXT         DEFAULT NULL,
    -- address
    address_line         VARCHAR(255) DEFAULT NULL,
    city                 VARCHAR(100) DEFAULT NULL,
    state                VARCHAR(100) DEFAULT NULL,
    country              VARCHAR(100) DEFAULT 'US',
    zip_code             VARCHAR(20)  DEFAULT NULL,
    latitude             DECIMAL(10, 7) DEFAULT NULL,
    longitude            DECIMAL(10, 7) DEFAULT NULL,
    -- contact
    phone                VARCHAR(30)  DEFAULT NULL,
    website              VARCHAR(512) DEFAULT NULL,
    email                VARCHAR(255) DEFAULT NULL,
    -- operational
    hours_of_operation   JSON        DEFAULT NULL,
    -- e.g. {"mon":"11:00-22:00","tue":"11:00-22:00",...,"sun":"closed"}
    pricing_tier         TINYINT UNSIGNED DEFAULT 2,  -- 1-4
    amenities            JSON        DEFAULT NULL,
    -- ["wifi","parking","outdoor_seating","reservations","wheelchair_accessible"]
    photos               JSON        DEFAULT NULL,   -- array of URLs
    -- aggregated stats (updated via trigger or app logic)
    avg_rating           DECIMAL(3,2) UNSIGNED DEFAULT 0.00,
    review_count         INT UNSIGNED          DEFAULT 0,
    is_active            TINYINT(1)            DEFAULT 1,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_rest_owner   FOREIGN KEY (owner_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_rest_addedby FOREIGN KEY (added_by) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_rest_owner       (owner_id),
    INDEX idx_rest_city        (city),
    INDEX idx_rest_cuisine     (cuisine_type),
    INDEX idx_rest_pricing     (pricing_tier),
    INDEX idx_rest_rating      (avg_rating),
    INDEX idx_rest_geo         (latitude, longitude),
    FULLTEXT INDEX ft_rest_name_desc (name, description)
) ENGINE=InnoDB;


-- =============================================================
-- 4. reviews
-- =============================================================
CREATE TABLE IF NOT EXISTS reviews (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id        INT UNSIGNED NOT NULL,
    restaurant_id  INT UNSIGNED NOT NULL,
    rating         TINYINT UNSIGNED NOT NULL,  -- 1-5
    comment        TEXT         DEFAULT NULL,
    photos         JSON         DEFAULT NULL,  -- array of URLs
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_rev_user  FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rev_rest  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- One review per user per restaurant
    UNIQUE KEY uq_user_restaurant (user_id, restaurant_id),
    INDEX idx_rev_user       (user_id),
    INDEX idx_rev_restaurant (restaurant_id),
    INDEX idx_rev_rating     (rating)
) ENGINE=InnoDB;


-- =============================================================
-- 5. favorites
-- =============================================================
CREATE TABLE IF NOT EXISTS favorites (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id        INT UNSIGNED NOT NULL,
    restaurant_id  INT UNSIGNED NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fav_user  FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_fav_rest  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    UNIQUE KEY uq_fav (user_id, restaurant_id),
    INDEX idx_fav_user       (user_id),
    INDEX idx_fav_restaurant (restaurant_id)
) ENGINE=InnoDB;


-- =============================================================
-- 6. conversation_history  (AI Assistant)
-- =============================================================
CREATE TABLE IF NOT EXISTS conversation_history (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    session_id  VARCHAR(64)  NOT NULL,    -- UUID generated per chat session
    role        ENUM('user','assistant','system') NOT NULL,
    message     TEXT         NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_conv_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_conv_user    (user_id),
    INDEX idx_conv_session (session_id),
    INDEX idx_conv_user_session (user_id, session_id)
) ENGINE=InnoDB;


-- =============================================================
-- SAMPLE DATA — System owner & 15 Bay Area Restaurants
-- =============================================================

-- System seed user (owner role for seeded restaurants)
INSERT INTO users (role, name, email, password_hash, city, state, country) VALUES
('owner', 'Seed Owner', 'seed@yelp-clone.local',
 '$2b$12$placeholderHashForSeedUser000000000000000000000',
 'San Francisco', 'CA', 'US');

-- Use the seeded owner's id (assumed 1) for all sample restaurants
INSERT INTO restaurants
    (owner_id, added_by, name, cuisine_type, description,
     address_line, city, state, zip_code, latitude, longitude,
     phone, website,
     hours_of_operation, pricing_tier, amenities,
     avg_rating, review_count)
VALUES
-- 1. Bix
(1, 1, 'Bix', 'American', 'Supper club atmosphere with craft cocktails and live jazz.',
 '56 Gold St', 'San Francisco', 'CA', '94133', 37.7955, -122.3997,
 '(415) 433-6300', 'https://bixrestaurant.com',
 '{"mon":"closed","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-23:00","sat":"17:30-23:00","sun":"closed"}',
 3, '["bar","reservations","live_music"]', 4.30, 1100),

-- 2. Zuni Café
(1, 1, 'Zuni Café', 'Mediterranean', 'Iconic SF bistro famous for brick-oven roast chicken and Caesar salad.',
 '1658 Market St', 'San Francisco', 'CA', '94102', 37.7739, -122.4193,
 '(415) 552-2522', 'https://zunicafe.com',
 '{"mon":"closed","tue":"11:30-23:00","wed":"11:30-23:00","thu":"11:30-23:00","fri":"11:30-00:00","sat":"11:00-00:00","sun":"11:00-23:00"}',
 3, '["outdoor_seating","bar","reservations"]', 4.40, 3200),

-- 3. Delfina
(1, 1, 'Delfina', 'Italian', 'Neighborhood Italian with house-made pasta and wood-fired pizza.',
 '3621 18th St', 'San Francisco', 'CA', '94110', 37.7615, -122.4262,
 '(415) 552-4055', 'https://delfinasf.com',
 '{"mon":"17:30-22:00","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-23:00","sat":"17:00-23:00","sun":"17:00-22:00"}',
 2, '["reservations","wheelchair_accessible"]', 4.50, 2800),

-- 4. State Bird Provisions
(1, 1, 'State Bird Provisions', 'American', 'Dim-sum-style California cuisine with ever-changing menu.',
 '1529 Fillmore St', 'San Francisco', 'CA', '94115', 37.7843, -122.4328,
 '(415) 795-1272', 'https://statebirdsf.com',
 '{"mon":"closed","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-22:00","sat":"17:30-22:00","sun":"17:30-22:00"}',
 3, '["reservations","bar"]', 4.60, 2400),

-- 5. Nopa
(1, 1, 'Nopa', 'American', 'Late-night farm-to-table staple with organic cocktails.',
 '560 Divisadero St', 'San Francisco', 'CA', '94117', 37.7739, -122.4376,
 '(415) 864-8643', 'https://nopasf.com',
 '{"mon":"17:00-01:00","tue":"17:00-01:00","wed":"17:00-01:00","thu":"17:00-01:00","fri":"17:00-01:00","sat":"10:00-01:00","sun":"10:00-01:00"}',
 2, '["outdoor_seating","bar","wheelchair_accessible"]', 4.40, 3600),

-- 6. Burma Superstar
(1, 1, 'Burma Superstar', 'Burmese', 'Beloved Burmese restaurant famous for tea leaf salad and rainbow salad.',
 '309 Clement St', 'San Francisco', 'CA', '94118', 37.7828, -122.4641,
 '(415) 387-2147', 'https://burmasuperstar.com',
 '{"mon":"11:00-22:00","tue":"11:00-22:00","wed":"11:00-22:00","thu":"11:00-22:00","fri":"11:00-22:00","sat":"11:00-22:00","sun":"11:00-22:00"}',
 2, '["wheelchair_accessible","takeout"]', 4.50, 4100),

-- 7. Chez Panisse
(1, 1, 'Chez Panisse', 'French', 'Alice Waters'' legendary Berkeley restaurant that pioneered California cuisine.',
 '1517 Shattuck Ave', 'Berkeley', 'CA', '94709', 37.8796, -122.2684,
 '(510) 548-5525', 'https://chezpanisse.com',
 '{"mon":"closed","tue":"17:30-21:00","wed":"17:30-21:00","thu":"17:30-21:00","fri":"17:30-21:30","sat":"17:00-21:30","sun":"closed"}',
 4, '["reservations","wheelchair_accessible"]', 4.70, 1800),

-- 8. Ramen Shop
(1, 1, 'Ramen Shop', 'Japanese', 'Craft ramen in Oakland with seasonal California-inspired toppings.',
 '4799 Shattuck Ave', 'Oakland', 'CA', '94609', 37.8475, -122.2630,
 '(510) 788-6370', 'https://ramenshopbar.com',
 '{"mon":"closed","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-22:30","sat":"17:30-22:30","sun":"17:30-21:00"}',
 2, '["bar","outdoor_seating"]', 4.50, 1600),

-- 9. Dio Deka
(1, 1, 'Dio Deka', 'Greek', 'Upscale Greek restaurant in Los Gatos with wood-grilled meats and fresh seafood.',
 '210 E Main Ave', 'Los Gatos', 'CA', '95030', 37.2241, -121.9803,
 '(408) 354-7700', 'https://diodeka.com',
 '{"mon":"17:00-21:00","tue":"17:00-21:00","wed":"17:00-21:00","thu":"17:00-21:00","fri":"17:00-22:00","sat":"12:00-22:00","sun":"12:00-21:00"}',
 4, '["reservations","outdoor_seating","bar","valet_parking"]', 4.40, 900),

-- 10. Manresa
(1, 1, 'Manresa', 'French', 'Michelin three-star tasting menu from chef David Kinch.',
 '320 Village Ln', 'Los Gatos', 'CA', '95030', 37.2251, -121.9797,
 '(408) 354-4330', 'https://manresarestaurant.com',
 '{"mon":"closed","tue":"closed","wed":"17:30-21:00","thu":"17:30-21:00","fri":"17:00-21:00","sat":"17:00-21:00","sun":"closed"}',
 4, '["reservations"]', 4.80, 650),

-- 11. Protégé
(1, 1, 'Protégé', 'American', 'Refined Californian tasting menu backed by Masters Sommeliers in Palo Alto.',
 '250 California Ave', 'Palo Alto', 'CA', '94306', 37.4271, -122.1441,
 '(650) 494-4181', 'https://protegepa.com',
 '{"mon":"closed","tue":"17:30-21:30","wed":"17:30-21:30","thu":"17:30-21:30","fri":"17:30-21:30","sat":"17:30-21:30","sun":"closed"}',
 4, '["reservations","bar","wheelchair_accessible"]', 4.50, 480),

-- 12. Flea Street Café
(1, 1, 'Flea Street Café', 'American', 'Organic farm-to-table dining in Menlo Park since 1980.',
 '3607 Alameda de las Pulgas', 'Menlo Park', 'CA', '94025', 37.4524, -122.1814,
 '(650) 854-1226', 'https://cooleatz.com',
 '{"mon":"closed","tue":"17:30-21:00","wed":"17:30-21:00","thu":"17:30-21:00","fri":"17:30-21:30","sat":"17:30-21:30","sun":"10:30-14:00"}',
 3, '["reservations","outdoor_seating"]', 4.30, 720),

-- 13. Plumed Horse
(1, 1, 'Plumed Horse', 'American', 'Award-winning wine cave dining with a farm-centric menu in Saratoga.',
 '14555 Big Basin Way', 'Saratoga', 'CA', '95070', 37.2638, -122.0229,
 '(408) 867-4711', 'https://plumedhorse.com',
 '{"mon":"closed","tue":"17:30-21:30","wed":"17:30-21:30","thu":"17:30-21:30","fri":"17:30-22:00","sat":"17:30-22:00","sun":"closed"}',
 4, '["reservations","bar","wine_cellar"]', 4.60, 560),

-- 14. Farmhouse Kitchen Thai
(1, 1, 'Farmhouse Kitchen Thai', 'Thai', 'Vibrant Thai restaurant with street-food-style dishes in a gorgeous space in SF.',
 '710 Florida St', 'San Francisco', 'CA', '94110', 37.7594, -122.4105,
 '(415) 814-2920', 'https://farmhousesf.com',
 '{"mon":"17:30-22:00","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-23:00","sat":"11:00-23:00","sun":"11:00-22:00"}',
 2, '["outdoor_seating","reservations","wheelchair_accessible","bar"]', 4.50, 2100),

-- 15. Flour + Water
(1, 1, 'Flour + Water', 'Italian', 'Mission District pasta hotspot celebrating Neapolitan cuisine with local ingredients.',
 '2401 Harrison St', 'San Francisco', 'CA', '94110', 37.7593, -122.4107,
 '(415) 826-7000', 'https://flourandwater.com',
 '{"mon":"17:30-22:00","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-23:00","sat":"17:00-23:00","sun":"17:00-22:00"}',
 3, '["reservations","bar","outdoor_seating"]', 4.60, 3300);

-- =============================================================
-- SAMPLE DATA — Restaurants from across the US
-- =============================================================
INSERT INTO restaurants
    (owner_id, added_by, name, cuisine_type, description,
     address_line, city, state, zip_code, latitude, longitude,
     phone, website,
     hours_of_operation, pricing_tier, amenities,
     avg_rating, review_count)
VALUES
-- New York, NY
(1, 1, 'Carbone', 'Italian', 'Old-school Italian-American red-sauce joint with a modern fine-dining twist in Greenwich Village.',
 '181 Thompson St', 'New York', 'NY', '10012', 40.7275, -74.0005,
 '(212) 254-3000', 'https://carbonenewyork.com',
 '{"mon":"17:30-23:00","tue":"17:30-23:00","wed":"17:30-23:00","thu":"17:30-23:00","fri":"17:30-23:30","sat":"17:30-23:30","sun":"17:30-22:00"}',
 4, '["reservations","bar","wheelchair_accessible"]', 4.60, 0),

(1, 1, 'Katz''s Delicatessen', 'American', 'Legendary Lower East Side deli serving pastrami and corned beef sandwiches since 1888.',
 '205 E Houston St', 'New York', 'NY', '10002', 40.7223, -73.9873,
 '(212) 254-2246', 'https://katzsdelicatessen.com',
 '{"mon":"08:00-22:45","tue":"08:00-22:45","wed":"08:00-22:45","thu":"08:00-22:45","fri":"08:00-02:45","sat":"08:00-02:45","sun":"08:00-22:45"}',
 2, '["takeout","wheelchair_accessible"]', 4.50, 0),

(1, 1, 'Le Bernardin', 'French', 'Michelin three-star seafood temple from chef Éric Ripert in Midtown Manhattan.',
 '155 W 51st St', 'New York', 'NY', '10019', 40.7617, -73.9814,
 '(212) 554-1515', 'https://le-bernardin.com',
 '{"mon":"12:00-14:30","tue":"12:00-14:30","wed":"12:00-14:30","thu":"12:00-14:30","fri":"12:00-14:30","sat":"17:00-22:30","sun":"closed"}',
 4, '["reservations","bar","private_dining"]', 4.80, 0),

(1, 1, 'Joe''s Pizza', 'American', 'Iconic Greenwich Village slice shop serving classic New York thin-crust pizza since 1975.',
 '7 Carmine St', 'New York', 'NY', '10014', 40.7303, -74.0025,
 '(212) 366-1182', 'https://joespizzanyc.com',
 '{"mon":"10:00-04:00","tue":"10:00-04:00","wed":"10:00-04:00","thu":"10:00-04:00","fri":"10:00-05:00","sat":"10:00-05:00","sun":"10:00-04:00"}',
 1, '["takeout","wheelchair_accessible"]', 4.40, 0),

-- Chicago, IL
(1, 1, 'Alinea', 'American', 'Grant Achatz''s avant-garde tasting menu experience — consistently rated among the world''s best.',
 '1723 N Halsted St', 'Chicago', 'IL', '60614', 41.9148, -87.6487,
 '(312) 867-0110', 'https://alinearestaurant.com',
 '{"mon":"closed","tue":"closed","wed":"17:00-21:00","thu":"17:00-21:00","fri":"17:00-21:00","sat":"17:00-21:00","sun":"closed"}',
 4, '["reservations"]', 4.90, 0),

(1, 1, 'Lou Malnati''s Pizzeria', 'American', 'Chicago''s beloved deep-dish institution, serving buttery crusts and chunky tomato sauce since 1971.',
 '439 N Wells St', 'Chicago', 'IL', '60654', 41.8899, -87.6340,
 '(312) 828-9800', 'https://loumalnatis.com',
 '{"mon":"11:00-22:00","tue":"11:00-22:00","wed":"11:00-22:00","thu":"11:00-22:00","fri":"11:00-23:00","sat":"11:00-23:00","sun":"12:00-22:00"}',
 2, '["takeout","delivery","wheelchair_accessible"]', 4.50, 0),

(1, 1, 'Girl & the Goat', 'American', 'Stephanie Izard''s West Loop flagship with bold shared plates and wood-fired flavors.',
 '800 W Randolph St', 'Chicago', 'IL', '60607', 41.8843, -87.6477,
 '(312) 492-6262', 'https://girlandthegoat.com',
 '{"mon":"16:00-22:00","tue":"16:00-22:00","wed":"16:00-22:00","thu":"16:00-22:00","fri":"16:00-23:00","sat":"16:00-23:00","sun":"closed"}',
 3, '["reservations","bar","outdoor_seating"]', 4.50, 0),

-- Austin, TX
(1, 1, 'Franklin Barbecue', 'American', 'James Beard Award-winning pitmaster Aaron Franklin''s legendary smoked brisket.',
 '900 E 11th St', 'Austin', 'TX', '78702', 30.2678, -97.7298,
 '(512) 653-1187', 'https://franklinbbq.com',
 '{"mon":"closed","tue":"11:00-15:00","wed":"11:00-15:00","thu":"11:00-15:00","fri":"11:00-15:00","sat":"11:00-15:00","sun":"11:00-15:00"}',
 2, '["outdoor_seating","takeout"]', 4.80, 0),

(1, 1, 'Uchi', 'Japanese', 'James Beard-winning sushi and Japanese small plates with creative Austin flair.',
 '801 S Lamar Blvd', 'Austin', 'TX', '78704', 30.2537, -97.7682,
 '(512) 916-4808', 'https://uchiaustin.com',
 '{"mon":"17:00-22:00","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-23:00","sat":"17:00-23:00","sun":"17:00-22:00"}',
 3, '["reservations","bar"]', 4.60, 0),

-- Seattle, WA
(1, 1, 'Canlis', 'American', 'Seattle''s storied fine-dining landmark with sweeping Lake Union views since 1950.',
 '2576 Aurora Ave N', 'Seattle', 'WA', '98109', 47.6418, -122.3466,
 '(206) 283-3313', 'https://canlis.com',
 '{"mon":"closed","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-22:00","sat":"17:00-22:00","sun":"closed"}',
 4, '["reservations","bar","valet_parking"]', 4.70, 0),

(1, 1, 'Pike Place Chowder', 'American', 'Award-winning chowders steps from the famous Pike Place Market.',
 '1530 Post Alley', 'Seattle', 'WA', '98101', 47.6093, -122.3421,
 '(206) 267-2537', 'https://pikeplacebowl.com',
 '{"mon":"10:00-17:00","tue":"10:00-17:00","wed":"10:00-17:00","thu":"10:00-17:00","fri":"10:00-17:00","sat":"09:00-17:00","sun":"09:00-17:00"}',
 1, '["takeout","outdoor_seating"]', 4.50, 0),

(1, 1, 'Nue', 'Mediterranean', 'Globally inspired small plates highlighting street foods from over 100 countries.',
 '1519 14th Ave', 'Seattle', 'WA', '98122', 47.6136, -122.3175,
 '(206) 257-0312', 'https://nueseattle.com',
 '{"mon":"16:00-22:00","tue":"16:00-22:00","wed":"16:00-22:00","thu":"16:00-22:00","fri":"16:00-23:00","sat":"16:00-23:00","sun":"16:00-21:00"}',
 2, '["bar","outdoor_seating","reservations"]', 4.30, 0),

-- Miami, FL
(1, 1, 'Versailles Restaurant', 'Cuban', 'Miami''s most famous Cuban restaurant, a Little Havana institution since 1971.',
 '3555 SW 8th St', 'Miami', 'FL', '33135', 25.7653, -80.2499,
 '(305) 444-0240', 'https://versaillesrestaurant.com',
 '{"mon":"08:00-01:00","tue":"08:00-01:00","wed":"08:00-01:00","thu":"08:00-01:00","fri":"08:00-02:30","sat":"08:00-02:30","sun":"09:00-01:00"}',
 2, '["outdoor_seating","takeout","wheelchair_accessible"]', 4.40, 0),

(1, 1, 'Zuma Miami', 'Japanese', 'Sleek izakaya-inspired rooftop dining with panoramic Brickell skyline views.',
 '270 Biscayne Blvd Way', 'Miami', 'FL', '33131', 25.7677, -80.1884,
 '(305) 577-0277', 'https://zumarestaurant.com',
 '{"mon":"12:00-15:00","tue":"12:00-15:00","wed":"12:00-15:00","thu":"12:00-15:00","fri":"12:00-16:00","sat":"12:30-16:00","sun":"12:30-15:30"}',
 4, '["reservations","bar","outdoor_seating","valet_parking"]', 4.50, 0),

-- New Orleans, LA
(1, 1, 'Dooky Chase''s Restaurant', 'American', 'Historic Creole institution in the Tremé neighborhood, a civil rights landmark since 1941.',
 '2301 Orleans Ave', 'New Orleans', 'LA', '70119', 29.9727, -90.0791,
 '(504) 821-0600', 'https://dookychaserestaurant.com',
 '{"mon":"closed","tue":"11:00-15:00","wed":"11:00-15:00","thu":"11:00-15:00","fri":"11:00-15:00","sat":"closed","sun":"closed"}',
 2, '["reservations","wheelchair_accessible"]', 4.50, 0),

(1, 1, 'Commander''s Palace', 'American', 'Iconic Garden District Creole landmark celebrated for jazz brunch and Creole classics.',
 '1403 Washington Ave', 'New Orleans', 'LA', '70130', 29.9285, -90.0847,
 '(504) 899-8221', 'https://commanderspalace.com',
 '{"mon":"11:30-21:00","tue":"11:30-21:00","wed":"11:30-21:00","thu":"11:30-21:00","fri":"11:30-22:00","sat":"10:00-22:00","sun":"10:00-21:00"}',
 4, '["reservations","bar","outdoor_seating","private_dining"]', 4.60, 0),

-- Boston, MA
(1, 1, 'Neptune Oyster', 'American', 'Tiny North End seafood bar famous for buttery lobster rolls and impeccably fresh oysters.',
 '63 Salem St', 'Boston', 'MA', '02113', 42.3639, -71.0554,
 '(617) 742-3474', 'https://neptuneoyster.com',
 '{"mon":"11:30-22:00","tue":"11:30-22:00","wed":"11:30-22:00","thu":"11:30-22:00","fri":"11:30-23:00","sat":"11:30-23:00","sun":"11:30-22:00"}',
 3, '["bar","outdoor_seating"]', 4.60, 0),

(1, 1, 'O Ya', 'Japanese', 'Intimate omakase with Japanese minimalism and New England ingredients in Downtown Boston.',
 '9 East St', 'Boston', 'MA', '02111', 42.3524, -71.0567,
 '(617) 654-9900', 'https://oyarestaurantboston.com',
 '{"mon":"closed","tue":"17:30-21:30","wed":"17:30-21:30","thu":"17:30-21:30","fri":"17:30-22:00","sat":"17:30-22:00","sun":"closed"}',
 4, '["reservations","bar"]', 4.70, 0),

-- Portland, OR
(1, 1, 'Le Pigeon', 'French', 'Gabriel Rucker''s James Beard-winning bistro with inventive French-American cooking.',
 '738 E Burnside St', 'Portland', 'OR', '97214', 45.5233, -122.6528,
 '(503) 546-8796', 'https://lepigeon.com',
 '{"mon":"closed","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-22:00","sat":"17:00-22:00","sun":"17:00-22:00"}',
 3, '["bar","reservations"]', 4.60, 0),

(1, 1, 'Pok Pok', 'Thai', 'Andy Ricker''s Northern Thai street-food landmark that sparked a national obsession with Thai cooking.',
 '3226 SE Division St', 'Portland', 'OR', '97202', 45.5043, -122.6320,
 '(503) 232-1387', 'https://pokpokpdx.com',
 '{"mon":"closed","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-22:00","sat":"17:00-22:00","sun":"17:00-22:00"}',
 2, '["outdoor_seating","bar"]', 4.40, 0),

-- Nashville, TN
(1, 1, 'Husk Nashville', 'American', 'Sean Brock''s temple to Southern cooking housed in a stunning Victorian mansion.',
 '37 Rutledge St', 'Nashville', 'TN', '37210', 36.1544, -86.7743,
 '(615) 256-6565', 'https://husknashville.com',
 '{"mon":"17:00-22:00","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"11:30-22:30","sat":"10:00-22:30","sun":"10:00-21:00"}',
 3, '["reservations","bar","outdoor_seating","wheelchair_accessible"]', 4.50, 0),

(1, 1, 'Prince''s Hot Chicken', 'American', 'The birthplace of Nashville hot chicken — fiery, crispy, iconic since the 1930s.',
 '123 Ewing Dr', 'Nashville', 'TN', '37207', 36.2009, -86.7621,
 '(615) 226-9442', 'https://princeshotchicken.com',
 '{"mon":"closed","tue":"closed","wed":"12:00-22:00","thu":"12:00-22:00","fri":"12:00-04:00","sat":"12:00-04:00","sun":"12:00-22:00"}',
 1, '["takeout"]', 4.40, 0),

-- Denver, CO
(1, 1, 'Snooze, an A.M. Eatery', 'American', 'Wildly creative pancake flights and inventive breakfast cocktails at this beloved Denver brunch spot.',
 '2262 Larimer St', 'Denver', 'CO', '80205', 39.7545, -104.9836,
 '(303) 297-0700', 'https://snoozeeatery.com',
 '{"mon":"06:30-14:30","tue":"06:30-14:30","wed":"06:30-14:30","thu":"06:30-14:30","fri":"06:30-14:30","sat":"06:30-14:30","sun":"06:30-14:30"}',
 2, '["outdoor_seating","wheelchair_accessible"]', 4.30, 0),

(1, 1, 'Fruition Restaurant', 'American', 'Chef Alex Seidel''s intimate farm-to-table gem in Denver''s Cherry Creek neighborhood.',
 '1313 E 6th Ave', 'Denver', 'CO', '80218', 39.7268, -104.9697,
 '(303) 831-1962', 'https://fruitionrestaurant.com',
 '{"mon":"closed","tue":"17:00-21:30","wed":"17:00-21:30","thu":"17:00-21:30","fri":"17:00-22:00","sat":"17:00-22:00","sun":"closed"}',
 3, '["reservations","bar"]', 4.50, 0),

-- Los Angeles, CA
(1, 1, 'Nobu Los Angeles', 'Japanese', 'Nobu Matsuhisa''s flagship Japanese-Peruvian fusion — the restaurant that started a global empire.',
 '903 N La Cienega Blvd', 'Los Angeles', 'CA', '90069', 34.0803, -118.3726,
 '(310) 657-5711', 'https://nobumatsuhisa.com',
 '{"mon":"17:45-22:15","tue":"17:45-22:15","wed":"17:45-22:15","thu":"17:45-22:15","fri":"17:45-23:00","sat":"17:45-23:00","sun":"17:45-22:15"}',
 4, '["reservations","bar"]', 4.50, 0),

(1, 1, 'Bestia', 'Italian', 'Rustic Italian charcuterie, hand-rolled pasta, and wood-roasted meats in the Arts District.',
 '2121 E 7th Pl', 'Los Angeles', 'CA', '90021', 34.0361, -118.2258,
 '(213) 514-5724', 'https://bestiala.com',
 '{"mon":"17:30-23:00","tue":"17:30-23:00","wed":"17:30-23:00","thu":"17:30-23:00","fri":"17:30-00:00","sat":"17:30-00:00","sun":"17:30-23:00"}',
 3, '["reservations","bar","outdoor_seating"]', 4.60, 0),

(1, 1, 'Gjusta', 'Mediterranean', 'All-day Venice Beach deli and bakery with extraordinary house-cured meats and pastries.',
 '320 Sunset Ave', 'Los Angeles', 'CA', '90291', 33.9974, -118.4716,
 '(310) 314-0320', 'https://gjusta.com',
 '{"mon":"07:00-21:00","tue":"07:00-21:00","wed":"07:00-21:00","thu":"07:00-21:00","fri":"07:00-21:00","sat":"07:00-21:00","sun":"07:00-21:00"}',
 2, '["outdoor_seating","takeout"]', 4.50, 0),

-- Atlanta, GA
(1, 1, 'Bacchanalia', 'American', 'Atlanta''s most celebrated fine-dining destination — contemporary American cuisine in a converted warehouse.',
 '1198 Howell Mill Rd NW', 'Atlanta', 'GA', '30318', 33.7876, -84.4138,
 '(404) 365-0410', 'https://starprovisions.com',
 '{"mon":"closed","tue":"closed","wed":"18:00-21:00","thu":"18:00-21:00","fri":"18:00-22:00","sat":"18:00-22:00","sun":"closed"}',
 4, '["reservations","bar"]', 4.70, 0),

(1, 1, 'Slutty Vegan', 'American', 'Atlanta''s viral plant-based burger joint with outrageous names and phenomenal flavors.',
 '1542 Ralph David Abernathy Blvd SW', 'Atlanta', 'GA', '30310', 33.7435, -84.4178,
 '(678) 500-6002', 'https://sluttyveganatl.com',
 '{"mon":"12:00-20:00","tue":"12:00-20:00","wed":"12:00-20:00","thu":"12:00-20:00","fri":"12:00-22:00","sat":"12:00-22:00","sun":"12:00-20:00"}',
 1, '["takeout","outdoor_seating"]', 4.30, 0);
