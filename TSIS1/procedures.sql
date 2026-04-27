CREATE OR REPLACE PROCEDURE add_phone_to_contact(p_contact_name VARCHAR, p_phone VARCHAR, p_type VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INT;
BEGIN
    SELECT user_id INTO v_id FROM phonetry2 WHERE user_name = p_contact_name;
    IF v_id IS NOT NULL THEN
        INSERT INTO phones (contact_id, phone, type) VALUES (v_id, p_phone, p_type);
    ELSE
        RAISE NOTICE 'Контакт % не найден', p_contact_name;
    END IF;
END;
$$;

--Процедура смены группы (с созданием группы, если её нет)
CREATE OR REPLACE PROCEDURE move_to_group(p_contact_name VARCHAR, p_group_name VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INT;
BEGIN
    -- Проверяем, есть ли такая группа, если нет — создаем
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;
    
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    -- Обновляем группу у контакта
    UPDATE phonetry2 SET group_id = v_group_id WHERE user_name = p_contact_name;
END;
$$;

-- 3. Функция глобального поиска (имя, email, телефоны)
CREATE OR REPLACE FUNCTION search_contacts_all(p_query TEXT)
RETURNS TABLE(u_name VARCHAR, u_email VARCHAR, u_phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT p.user_name, p.email, ph.phone
    FROM phonetry2 p
    LEFT JOIN phones ph ON p.user_id = ph.contact_id
    WHERE p.user_name ILIKE '%' || p_query || '%'
       OR p.email ILIKE '%' || p_query || '%'
       OR ph.phone ILIKE '%' || p_query || '%';
END;
$$ LANGUAGE plpgsql;