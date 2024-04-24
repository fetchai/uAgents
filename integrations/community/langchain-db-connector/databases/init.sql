\c postgres;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'postgres'
    ) THEN
        CREATE DATABASE postgres;
    END IF;
END
$$;

\c postgres;

DROP TABLE IF EXISTS agents_by_user;

CREATE TABLE IF NOT EXISTS agents_by_user (
    id                       SERIAL PRIMARY KEY,
    user_id                  VARCHAR(100),
    agent_address            VARCHAR(100),
    name                     TEXT,
    domain_name              TEXT,
    readme                   TEXT,
    running                  BOOLEAN,
    compiled                 BOOLEAN,
    agent_code_digest        VARCHAR(100),
    code_update_timestamp    TIMESTAMP,
    wallet_address           VARCHAR(100),
    protocols                TEXT[]
);

INSERT INTO agents_by_user (
    user_id,
    agent_address,
    name,
    domain_name,
    readme,
    running,
    compiled,
    agent_code_digest,
    code_update_timestamp,
    wallet_address,
    protocols
) VALUES (
    'user1',
    'agent1qvczp4c2dljq34jllfvdg7f4j2fp54m8d4y4wtmv8p3fu3tehtcnq9shzgn',
    'Near Restaurant Booking',
    '',
    'Hi I am a basic restaurant agent. Query me to receive restaurants near you.',
    true,
    true,
    '',
    CURRENT_TIMESTAMP,
    'fetch1f0vu7zu4fep7yy5v2fc7ah7ak9j2mclf7ah8e5',
    ARRAY['059a16b7a9986d36abf62a03c3a20270671772255b40e7f40663f5471837d360', 'a98290009c0891bc431c5159357074527d10eff6b2e86a61fcf7721b472f1125']
);


INSERT INTO agents_by_user (
    user_id,
    agent_address,
    name,
    domain_name,
    readme,
    running,
    compiled,
    agent_code_digest,
    code_update_timestamp,
    wallet_address,
    protocols
) VALUES (
    'user2',
    'agent1qgr30tglepwmx27xn5vdq3znv3yuqfa73wykpaay033xu6ypgzw7vzwvyyq',
    'Spam Agent Alice',
    '',
    'Hi I am Alice. I will spam agentverse with a lot of transactions. See how many I have reached above the readme.',
    true,
    true,
    '',
    CURRENT_TIMESTAMP,
    '',
    ARRAY['059a16b7a9986d36abf62a03c3a20270671772255b40e7f40663f5471837d360', 'a98290009c0891bc431c5159357074527d10eff6b2e86a61fcf7721b472f1125']
);

INSERT INTO agents_by_user (
    user_id,
    agent_address,
    name,
    domain_name,
    readme,
    running,
    compiled,
    agent_code_digest,
    code_update_timestamp,
    wallet_address,
    protocols
) VALUES (
    'user3',
    'agent1q04sr3z0f4ads884jt7jtfvjy8deq95xdmc9ynwa8clmdc39jw4u6vdh3jz',
    'Flight Offer and Booking Execution',
    '',
    'Hi I am your agent if you are looking for flights! I can help you find the best offers and book them for you.',
    true,
    true,
    '',
    CURRENT_TIMESTAMP,
    '',
    ARRAY['a3b72d335ebfd05f197b43e631ea42b8b4583de74f714870e316e169e0ce15aa', 'e518940bddc9864ef3543d6e61dd7775a0442d612f6c11de0958c0bd122e8a81']
);


INSERT INTO agents_by_user (
    user_id,
    agent_address,
    name,
    domain_name,
    readme,
    running,
    compiled,
    agent_code_digest,
    code_update_timestamp,
    wallet_address,
    protocols
) VALUES (
    'user3',
    'agent1qfwu306y9zlzfrqegtm3jw284jsywhrj0phmkdf2u9cjqc2v903kszvqht8',
    'I am a blank agent',
    '',
    '',
    true,
    true,
    '',
    CURRENT_TIMESTAMP,
    '',
    ARRAY['a3b72d335ebfd05f197b43e631ea42b8b4583de74f714870e316e169e0ce15aa', 'e518940bddc9864ef3543d6e61dd7775a0442d612f6c11de0958c0bd122e8a81']
);
