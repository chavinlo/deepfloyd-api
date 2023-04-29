from main import config
from utilities.general import fail, succ

def noInputDeepfloyd(req: dict) -> tuple[bool, dict]:
        defaults = config['defaults']

        if "prompt" not in req:
            return False, fail("MANATORY_PARAM_NOT_FOUND", f"prompt")
            
        for key, data in defaults.items():
            if key not in req and key != "model":
                req[key] = data

        for key, data in req.items():
            if key == "negative_prompt":
                if type(data) is not str:
                    return False, fail("INVALID_PARAM_TYPE", "negative_prompt")

            if key == "steps":
                if type(data) is not dict:
                    return False, fail("INVALID_PARAM_TYPE", "steps")
                if 'stage_2' not in data:
                    req['steps']['stage_2'] = int(req['steps']['stage_1']/2)
                    if req['steps']['stage_2'] < 50:
                        req['steps']['stage_2'] = 50
                #iterate inside dict
                for key_in, data_in in req['steps'].items():
                    if key_in == 'stage_1':
                        if type(data_in) is not int:
                            return False, fail("INVALID_PARAM_TYPE", "steps;stage_1")
                        else:
                            if data_in > 110 or data_in < 20:
                                return False, fail("INVALID_RANGE", "steps;STEPS_MUST_BE_ABOVE_20_AND_BELOW_70")
                            
                    if key_in == 'stage_2':
                            if type(data_in) is not int:
                                return False, fail("INVALID_PARAM_TYPE", "steps;stage_2")
                            else:
                                if data_in > 110 or data_in < 20:
                                    return False, fail("INVALID_RANGE", "steps;STEPS_MUST_BE_ABOVE_20_AND_BELOW_70")

            if key == "guidance":
                if type(data) is not float:
                    if type(data) is not int:
                        return False, fail("INVALID_PARAM_TYPE", "guidance")
                    else:
                        data = float(data)
                if data < 2.0 or data > 15.0:
                    return False, fail("INVALID_ARGUMENT", "guidance;GUIDANCE_MUST_BE_ABOVE_2.0_AND_BELOW_15.0")
                    
            if key == "seed":
                if type(data) is not int:
                    return False, fail("INVALID_PARAM_TYPE", "seed")
            
        return True, req