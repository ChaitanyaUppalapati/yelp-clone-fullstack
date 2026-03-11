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
