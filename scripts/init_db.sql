-- 初始化数据库脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(200) NOT NULL,
    avatar_url TEXT,
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户学科进度
CREATE TABLE IF NOT EXISTS user_subject_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(100),
    mastery_level INT DEFAULT 0,
    total_exp BIGINT DEFAULT 0,
    last_study_at TIMESTAMPTZ,
    UNIQUE(user_id, subject_id)
);

CREATE INDEX idx_user_subject_progress_user ON user_subject_progress(user_id);
CREATE INDEX idx_user_subject_progress_subject ON user_subject_progress(subject_id);

-- 用户货币
CREATE TABLE IF NOT EXISTS user_currency (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    currency_type VARCHAR(50) NOT NULL,
    amount BIGINT DEFAULT 0,
    UNIQUE(user_id, currency_type)
);

-- 学科配置
CREATE TABLE IF NOT EXISTS subjects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    agent_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认学科
INSERT INTO subjects (id, name, description, is_active) VALUES
    ('history', '历史', '穿越时空，亲历历史现场', TRUE),
    ('physics', '物理', '探索万物运行的奥秘', FALSE),
    ('math', '数学', '思维的体操', FALSE),
    ('chemistry', '化学', '微观世界的奥秘', FALSE)
ON CONFLICT (id) DO NOTHING;

-- 教材版本
CREATE TABLE IF NOT EXISTS textbooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(50) NOT NULL REFERENCES subjects(id),
    publisher VARCHAR(100),
    grade VARCHAR(50),
    version_year INT,
    file_path TEXT,
    parsed_data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 知识点
CREATE TABLE IF NOT EXISTS knowledge_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(50) NOT NULL,
    textbook_id UUID REFERENCES textbooks(id),
    chapter_id VARCHAR(100),
    section_id VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    difficulty INT DEFAULT 1,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_points_subject ON knowledge_points(subject_id);
CREATE INDEX idx_knowledge_points_chapter ON knowledge_points(chapter_id);

-- 学习记录
CREATE TABLE IF NOT EXISTS study_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id VARCHAR(50) NOT NULL,
    knowledge_point_id UUID,
    activity_type VARCHAR(50) NOT NULL,
    score INT,
    time_spent INT,
    exp_gained INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_study_records_user ON study_records(user_id);
CREATE INDEX idx_study_records_subject ON study_records(subject_id);

-- 成就定义
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    condition_type VARCHAR(50) NOT NULL,
    condition_value INT NOT NULL,
    reward_exp INT DEFAULT 0,
    reward_currency JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE
);

-- 用户成就
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id),
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- 任务定义
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty INT DEFAULT 1,
    reward_exp INT DEFAULT 0,
    reward_currency JSONB DEFAULT '{}',
    conditions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户任务进度
CREATE TABLE IF NOT EXISTS user_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id),
    status VARCHAR(20) DEFAULT 'pending',
    progress JSONB DEFAULT '{}',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户学伴
CREATE TABLE IF NOT EXISTS user_companions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    companion_type VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    mood INT DEFAULT 100,
    appearance JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 签到记录
CREATE TABLE IF NOT EXISTS checkin_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_date VARCHAR(10) NOT NULL,
    streak_days INT DEFAULT 1,
    exp_gained INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, checkin_date)
);

CREATE INDEX idx_checkin_records_user ON checkin_records(user_id);
