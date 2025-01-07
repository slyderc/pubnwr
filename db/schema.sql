-- PubNWR Database Schema

-- Enable foreign keys and other SQLite features
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Realtime tracking of published tracks
CREATE TABLE IF NOT EXISTS realtime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    UNIQUE(service, artist, title)
);

-- Create index for timestamp lookups
CREATE INDEX IF NOT EXISTS idx_realtime_timestamp ON realtime(timestamp);

-- SoundExchange reporting table
CREATE TABLE IF NOT EXISTS soundexchange (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    featured_artist TEXT NOT NULL,
    sound_recording_title TEXT NOT NULL,
    ISRC TEXT,
    album_title TEXT,
    marketing_label TEXT,
    actual_total_performances INTEGER DEFAULT 1,
    timestamp INTEGER NOT NULL
);

-- Create indexes for SoundExchange queries
CREATE INDEX IF NOT EXISTS idx_soundexchange_artist ON soundexchange(featured_artist);
CREATE INDEX IF NOT EXISTS idx_soundexchange_title ON soundexchange(sound_recording_title);
CREATE INDEX IF NOT EXISTS idx_soundexchange_timestamp ON soundexchange(timestamp);

-- Program tracking
CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    presenter TEXT,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    tracks_played INTEGER DEFAULT 0
);

-- Create index for program queries
CREATE INDEX IF NOT EXISTS idx_programs_time ON programs(start_time, end_time);

-- Track history for analytics
CREATE TABLE IF NOT EXISTS track_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT,
    program_id INTEGER,
    play_time INTEGER NOT NULL,
    FOREIGN KEY(program_id) REFERENCES programs(id)
);

-- Create indexes for history queries
CREATE INDEX IF NOT EXISTS idx_history_artist ON track_history(artist);
CREATE INDEX IF NOT EXISTS idx_history_play_time ON track_history(play_time);

-- Statistics table for analytics
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    program_id INTEGER,
    listener_count INTEGER DEFAULT 0,
    FOREIGN KEY(program_id) REFERENCES programs(id)
);

-- Create index for statistics queries
CREATE INDEX IF NOT EXISTS idx_statistics_timestamp ON statistics(timestamp);

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_recent_tracks AS
SELECT 
    th.artist,
    th.title,
    th.album,
    th.play_time,
    p.name as program_name,
    p.presenter
FROM track_history th
LEFT JOIN programs p ON th.program_id = p.id
ORDER BY th.play_time DESC
LIMIT 100;

CREATE VIEW IF NOT EXISTS v_program_statistics AS
SELECT 
    p.name as program_name,
    p.presenter,
    COUNT(th.id) as tracks_played,
    AVG(s.listener_count) as avg_listeners,
    MAX(s.listener_count) as peak_listeners
FROM programs p
LEFT JOIN track_history th ON th.program_id = p.id
LEFT JOIN statistics s ON s.program_id = p.id
GROUP BY p.id
ORDER BY p.start_time DESC;

-- Cleanup function
CREATE TRIGGER IF NOT EXISTS cleanup_old_data
AFTER INSERT ON realtime
BEGIN
    -- Delete realtime entries older than 7 days
    DELETE FROM realtime 
    WHERE timestamp < strftime('%s', 'now', '-7 days');
    
    -- Keep only last 1000 track history entries
    DELETE FROM track_history 
    WHERE id NOT IN (
        SELECT id FROM track_history 
        ORDER BY play_time DESC 
        LIMIT 1000
    );
    
    -- Delete statistics older than 90 days
    DELETE FROM statistics 
    WHERE timestamp < strftime('%s', 'now', '-90 days');
END;

